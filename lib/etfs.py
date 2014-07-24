###########
# IMPORTS #
###########

import os
import json
import uuid
import ystockquote


##############
# PUBLIC API #
##############

def etf_json():
    return json.dumps(_formatted_etfs())

def quotes_json():
    etf_tickers = [ etf['ticker'] for etf in _etfs() ]
    quotes = { "quotes": _get_quotes(etf_tickers) }
    return json.dumps(quotes)


###############
# PRIVATE API #
###############

def _etfs():
    this_dir = os.path.dirname(__file__)
    json_dir = os.path.join(this_dir, os.pardir, 'config')
    etfs_file_path = os.path.join(json_dir, 'etfs.json')

    with open(etfs_file_path) as data_file:
        etf_list = json.load(data_file)
    return etf_list

def _formatted_etfs():
    # Create formatted etf data to be returned from /etfs. Put it in an object
    # as otherwise python won't want to load it.
    def uuid_for(ticker):
        encoded = ticker.encode('utf-8')
        return uuid.uuid5(uuid.NAMESPACE_DNS, encoded).hex

    def add_id_to_etf(etf):
        etf['id'] = uuid_for(etf['ticker'])
        return etf

    return {
        "etfs": [
            add_id_to_etf(etf) for etf in _etfs()
        ]
    }

def _get_quotes(tickers):
    return { ticker: float(ystockquote.get_price(ticker)) for ticker in tickers }
