#########

import os
import redis

from flask import Flask
from flask import jsonify

from flask_environments import Environments

#########

app = Flask(__name__)

#########

env = Environments(app)
env.from_yaml(os.path.join(os.path.dirname(__file__), 'config', 'config.yml'))

#########

redis_url   = os.getenv('REDIS_URL', app.config['DATABASE'])
redis_conn  = redis.StrictRedis.from_url(redis_url)

#########

@app.route('/')
def root():
    return 'Hello World!'

@app.route('/securities/<ticker>')
def ticker(ticker):
    list = [
        {'a': 1, 'b': 2},
        {'a': 5, 'b': 10}
    ]
    return jsonify({
        'results': {
            'list':     list,
            'ticker':   ticker
        }
    })

if __name__ == '__main__':
    app.run()
