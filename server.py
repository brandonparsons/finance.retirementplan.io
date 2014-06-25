###########
# IMPORTS #
###########

import os
import redis
import pandas as pd

from flask import Flask
from flask import request
from flask import jsonify
from flask import abort

from flask_environments import Environments
from flask_sslify import SSLify

from lib.efficient_frontier import efficient_frontier


###############
# ENVIRONMENT #
###############

app = Flask(__name__)

env = Environments(app)
env.from_yaml(os.path.join(os.path.dirname(__file__), 'config', 'config.yml'))

sslify = SSLify(app)

redis_url   = os.getenv('REDIS_URL', app.config['REDIS_URL'])
redis_conn  = redis.StrictRedis.from_url(redis_url)


###################
# UTILITY METHODS #
###################

def check_for_authorization():
  auth_token = os.getenv('AUTH_TOKEN', app.config['AUTH_TOKEN'])
  provided_token = request.headers.get('Authorization') or request.args.get('auth_token')
  if (provided_token and provided_token == auth_token):
    return True
  else:
    return abort(403)

def covariance_matrix(tickers):
    # Covariance matrix is a *DataFrame*
    json = redis_conn.get('covariance_matrix')
    df = pd.io.json.read_json(json)

    tickers_set = set(tickers)
    available_tickers_set = set(df.index.values)
    tickers_to_eliminate = list(available_tickers_set - tickers_set)

    return df.drop(tickers_to_eliminate, axis=0).drop(tickers_to_eliminate, axis=1)

def mean_returns(tickers):
    # Mean returns is a *Series*
    json = redis_conn.get('mean_returns')
    df = pd.io.json.read_json(json, typ='series')

    tickers_set = set(tickers)
    available_tickers_set = set(df.index.values)
    tickers_to_eliminate = list(available_tickers_set - tickers_set)

    return df.drop(tickers_to_eliminate)


##########
# ROUTES #
##########

@app.route('/')
def root():
    return 'Hello World!'

@app.route('/health')
def health():
    return "OK", 200

@app.route('/calc', methods=["POST"])
def cla_calc_route():
    check_for_authorization()

    j       = request.json
    tickers = j['tickers']

    app.logger.info("Received CLA calc request for tickers: %s" % tickers)

    means   = mean_returns(tickers)
    covars  = covariance_matrix(tickers)

    return jsonify( efficient_frontier(tickers, means, covars) )


##########
# LOADER #
##########

if __name__ == '__main__':
    app.run()
