###########
# IMPORTS #
###########

import os
import json
import redis
import pandas as pd

from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from flask import abort

from flask_sslify import SSLify

from lib.efficient_frontier import efficient_frontier


###############
# ENVIRONMENT #
###############

app = Flask(__name__)

app.config['DEBUG'] = os.environ.get('DEBUG', False)

if not app.config['DEBUG']:
    sslify = SSLify(app)

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
    # Covariance matrix is a *DataFrame*
    json = redis_conn.get('covariance_matrix')
    df   = pd.io.json.read_json(json)

    asset_ids_set             = set(asset_ids)
    available_asset_ids_set   = set(df.index.values)
    asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)

    return df.drop(asset_ids_to_eliminate, axis=0).drop(asset_ids_to_eliminate, axis=1)

def cholesky_decomposition(asset_ids):
    # Cholesky decomp matrix is a *DataFrame*
    json = redis_conn.get('cholesky_decomposition')
    df   = pd.io.json.read_json(json)

    asset_ids_set             = set(asset_ids)
    available_asset_ids_set   = set(df.index.values)
    asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)

    return df.drop(asset_ids_to_eliminate, axis=0).drop(asset_ids_to_eliminate, axis=1)

def mean_returns(asset_ids):
    # Mean returns is a *Series*
    json = redis_conn.get('mean_returns')
    df   = pd.io.json.read_json(json, typ='series')

    asset_ids_set             = set(asset_ids)
    available_asset_ids_set   = set(df.index.values)
    asset_ids_to_eliminate    = list(available_asset_ids_set - asset_ids_set)

    return df.drop(asset_ids_to_eliminate)

def build_efficient_frontier_for(asset_ids):
    means    = mean_returns(asset_ids)
    covars   = covariance_matrix(asset_ids)
    return efficient_frontier(asset_ids, means, covars)


##########
# ROUTES #
##########

# Health check routes

@app.route('/')
def root():
    return 'Hello World!'

@app.route('/health')
def health():
    return "OK", 200

# App routes

@app.route('/assets', methods=['GET'])
def assets_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('asset_list')) )

@app.route('/etfs', methods=['GET'])
def etfs_route():
    check_for_authorization()
    return jsonify( json.loads(redis_conn.get('etf_list')) )

@app.route('/cholesky', methods=['GET'])
def cholesky_route():
    check_for_authorization()
    asset_ids = get_key_in_json('asset_ids', request.json)
    app.logger.info("Received cholesky request for: %s" % asset_ids)
    cholesky_dataframe_as_array = cholesky_decomposition(asset_ids).values
    as_flat_array = cholesky_dataframe_as_array.flatten().tolist() # Just do .tolist() if you want it as an array of arrays
    return jsonify( { "cholesky_decomposition": as_flat_array } )

@app.route('/calc', methods=["POST"])
def cla_calc_route():
    check_for_authorization()
    asset_ids = get_key_in_json('asset_ids', request.json)
    app.logger.info("Received CLA calc request for: %s" % asset_ids)
    return jsonify(build_efficient_frontier_for(asset_ids))


##########
# LOADER #
##########

if __name__ == '__main__':
    app.run()
