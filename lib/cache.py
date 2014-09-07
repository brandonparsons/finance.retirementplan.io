###########
# IMPORTS #
###########

from __future__ import absolute_import

import os
import requests


##############
# PUBLIC API #
##############

def clear():
    requests.get( _cache_url() , headers={'Authorization': _auth_token()} )
    return True


###############
# PRIVATE API #
###############

def _cache_url():
    self_url = os.environ.get('SELF_URL', 'http://rp-finance.dev')
    return self_url + '/clear_cache'

def _auth_token():
    auth_token = os.environ.get('AUTH_TOKEN', 'abcd')
    return auth_token
