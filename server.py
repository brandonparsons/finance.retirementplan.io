###########
# IMPORTS #
###########

from __future__ import absolute_import

import os
import json
import redis
import bmemcached
import hashlib

from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from flask import abort

from flask_sslify import SSLify

import pandas as pd

from lib.efficient_frontier import efficient_frontier


###############
# ENVIRONMENT #
###############

app = Flask(__name__)

app.config['DEBUG'] = os.environ.get('DEBUG', False)

# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xviii-deployment-on-the-heroku-cloud
if not app.config['DEBUG']:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)

if not app.config['DEBUG']:
    app.logger.info("Forcing SSL")
    sslify = SSLify(app)

if app.config['DEBUG']:
    cache = bmemcached.Client(servers=['127.0.0.1:11211'])
else:
    cache = bmemcached.Client(
                servers=os.environ['MEMCACHEDCLOUD_SERVERS'].split(","),
                username=os.environ['MEMCACHEDCLOUD_USERNAME'],
                password=os.environ['MEMCACHEDCLOUD_PASSWORD']
            )

redis_conn = redis.StrictRedis.from_url(os.environ['REDIS_URL'])


###################
# UTILITY METHODS #
###################

def check_for_authorization():
    auth_token = os.environ['AUTH_TOKEN']
    provided_token = request.headers.get('Authorization') or request.args.get('auth_token')
    if (provided_token and provided_token == auth_token):
        return True
    else:
        return abort(403)

def get_key_in_json(key, json):
    if json is None:
        return abort(400)
    if key not in json:
        return abort(422)
    return json[key]


######################
# APP HELPER METHODS #
######################

def covariance_matrix(asset_ids):
    # No need to memoize this unless jsonify is taking lots of time - data from redis
    # Covariance matrix is a *DataFrame*
    json = redis_conn.get('covariance_matrix')
    df   = pd.io.json.read_json(json)

    asset_ids_set             = set(asset_ids)
    available_asset_ids_set   = set(df.index.values)
    asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)

    return df.drop(asset_ids_to_eliminate, axis=0).drop(asset_ids_to_eliminate, axis=1)

def cholesky_decomposition(asset_ids):
    # No need to memoize this unless jsonify is taking lots of time - data from redis
    # Cholesky decomp matrix is a *DataFrame*
    json = redis_conn.get('cholesky_decomposition')
    df   = pd.io.json.read_json(json)

    asset_ids_set             = set(asset_ids)
    available_asset_ids_set   = set(df.index.values)
    asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)

    return df.drop(asset_ids_to_eliminate, axis=0).drop(asset_ids_to_eliminate, axis=1)

def mean_returns(asset_ids, returns_source):
    """
    Grabs mean return data, and returns a dataframe with only the relavant columns
    :param asset_ids: array of asset ID's (e.g. INTL-STOCK)
    :param returns_source: Which data we are interested in - one of: 'reverse_optimized_returns', 'mean_returns', 'five_year_returns'
    """

    # No need to memoize this unless jsonify is taking lots of time - data from redis
    # Mean returns is a *Series*
    json = redis_conn.get(returns_source)
    df   = pd.io.json.read_json(json, typ='series')

    if len(asset_ids) > 0:
        asset_ids_set             = set(asset_ids)
        available_asset_ids_set   = set(df.index.values)
        asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)
        return df.drop(asset_ids_to_eliminate)
    else:
        return df

def std_dev_returns(asset_ids):
    # No need to memoize this unless jsonify is taking lots of time - data from redis
    # Mean returns is a *Series*
    json = redis_conn.get('std_dev_returns')
    df   = pd.io.json.read_json(json, typ='series')

    if len(asset_ids) > 0:
        asset_ids_set             = set(asset_ids)
        available_asset_ids_set   = set(df.index.values)
        asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)
        return df.drop(asset_ids_to_eliminate)
    else:
        return df

def build_efficient_frontier_for(asset_ids, use_market_implied_returns=True):
    md5Hash = hashlib.md5("-".join(asset_ids)).hexdigest()
    cache_key = "efficient_frontier/" + md5Hash + "/" + ("implied" if use_market_implied_returns else "historical")
    val = cache.get(cache_key)
    if val is None:
        app.logger.info("[Cache Miss] Building efficient frontier for: %s" % asset_ids)
        if use_market_implied_returns:
            asset_returns = mean_returns(asset_ids, returns_source="reverse_optimized_returns")
        else:
            asset_returns = mean_returns(asset_ids, returns_source="mean_returns")
        covars = covariance_matrix(asset_ids)
        historical_returns = mean_returns(asset_ids, returns_source="five_year_returns")
        frontier = efficient_frontier(asset_ids, asset_returns, historical_returns, covars)
        # FIXME: You are json dumping to store in memcache, marshalling to return
        # to request, then flask-jsonifying back again. Better way? For later......
        cache.set(cache_key, json.dumps(frontier))
    else:
        app.logger.info("[Cache Hit] Retreiving efficient frontier for: %s" % asset_ids)
        # FIXME: You are json dumping to store in memcache, marshalling to return
        # to request, then flask-jsonifying back again. Better way? For later......
        frontier = json.loads(val)

    # app.logger.info("Frontier: %r" % frontier)
    return frontier


##########
# ROUTES #
##########

# Utility routes

@app.route('/')
def root():
    return 'Hello World!'

@app.route('/health')
def health():
    return "OK", 200

@app.route('/clear_cache', methods=["GET"])
def clear_cache():
  check_for_authorization()
  cache.flush_all()
  return jsonify({"success": True, "message": "Cache cleared."})


# App routes

@app.route('/assets', methods=['GET'])
def assets_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('asset_list')) )

@app.route('/etfs', methods=['GET'])
def etfs_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('etf_list')) )

@app.route('/performance', methods=['GET'])
def performance_route():
    check_for_authorization()
    asset_ids = get_key_in_json('asset_ids', request.json)
    asset_ids.sort()
    df = pd.DataFrame()
    df['mean'] = mean_returns(asset_ids, returns_source="reverse_optimized_returns")
    df['historical_mean'] = mean_returns(asset_ids, returns_source="mean_returns")
    df['five_year_mean'] = mean_returns(asset_ids, returns_source="five_year_returns")
    df['std_dev'] = std_dev_returns(asset_ids)
    return Response(df.transpose().to_json(), mimetype='application/json')

@app.route('/quotes', methods=['GET'])
def quotes_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('quotes')) )

@app.route('/inflation', methods=['GET'])
def inflation_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('inflation')) )

@app.route('/real_estate', methods=['GET'])
def real_estate_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('real_estate')) )

@app.route('/cholesky', methods=['GET'])
def cholesky_route():
    check_for_authorization()
    asset_ids = get_key_in_json('asset_ids', request.json)
    asset_ids.sort()
    app.logger.info("Received cholesky request for: %s" % asset_ids)
    cholesky_dataframe_as_array = cholesky_decomposition(asset_ids).values
    as_flat_array = cholesky_dataframe_as_array.flatten().tolist() # Just do .tolist() if you want it as an array of arrays
    return jsonify( { "cholesky_decomposition": as_flat_array } )

@app.route('/efficient_frontier', methods=["GET"])
def efficient_frontier_route():
    check_for_authorization()
    asset_ids = get_key_in_json('asset_ids', request.json)
    asset_ids.sort()
    app.logger.info("Received CLA Efficient Frontier request for: %s" % asset_ids)
    return jsonify(build_efficient_frontier_for(asset_ids))


##########
# LOADER #
##########

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)
