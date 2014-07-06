import os
import json
import redis

import lib.load_json_data as load_json_data
import lib.source_data as source_data
import lib.stats as stats


#################

print("Updating securities data in Redis....")

redis_url   = os.getenv('REDIS_URL')
if redis_url is None:
    raise KeyError("%s not present" % "REDIS_URL")
redis_conn  = redis.StrictRedis.from_url(redis_url)

#################

# Load and format asset classes

assets  = load_json_data.get_assets()

# Create formatted asset data to be returned from /assets. Put it in an object
# as otherwise python won't want to load it.
def asset_without_representative_ticker(asset):
    tmp = asset.copy()
    del tmp['representative_ticker']
    return tmp

formatted_asset_data = {
    "assets": [
        asset_without_representative_ticker(el) for el in assets
    ]
}

#################

# Get prices from external data source
tickers = [ el['representative_ticker'] for el in assets ]
prices = source_data.get_prices(tickers)

# Crunch statistics
mean_returns, std_dev_returns, covariance_matrix = stats.generate_stats(prices)

#################

# Load and format the ETFs as well
etfs = load_json_data.get_etfs()

def slugize_ticker(ticker):
    return ticker.replace('.', '-').upper()

def add_id_to_etf(etf):
    etf['id'] = slugize_ticker(etf['ticker'])
    return etf

# Create formatted etf data to be returned from /etfs. Put it in an object
# as otherwise python won't want to load it.
formatted_etfs = {
    "etfs": [
        add_id_to_etf(etf) for etf in etfs
    ]
}

#################

# Before we store the data into redis, swap the tickers for asset IDs so that
# the whole algorithm is ticker-independent

# Sort everything so we can be sure we are replacing in the correct order
mean_returns    = mean_returns.sort_index()
std_dev_returns = std_dev_returns.sort_index()
covariance_matrix.sort_index(axis=0, inplace=True)
covariance_matrix.sort_index(axis=1, inplace=True)
tickers.sort()


# Build up the corresponding list of asset-ids to replace with
replacement_values = []
for ticker in tickers:
    relevant_asset_dict_index = next(index for (index, d) in enumerate(assets) if d['representative_ticker'] == ticker)
    asset_dict = assets[relevant_asset_dict_index]
    replacement_values.append(asset_dict['id'])

mean_returns.index        = replacement_values
std_dev_returns.index     = replacement_values
covariance_matrix.index   = replacement_values
covariance_matrix.columns = replacement_values

# Re-sort the newly renamed dataframes/series
mean_returns    = mean_returns.sort_index()
std_dev_returns = std_dev_returns.sort_index()
covariance_matrix.sort_index(axis=0, inplace=True)
covariance_matrix.sort_index(axis=1, inplace=True)

#################

# Save data to redis. Execute as multi to keep data consistency
pipe = redis_conn.pipeline()
pipe.multi()

##
pipe.set(name='mean_returns',      value=mean_returns.to_json())
pipe.set(name='std_dev_returns',   value=std_dev_returns.to_json())
pipe.set(name='covariance_matrix', value=covariance_matrix.to_json())
##
pipe.set(name='asset_list', value=json.dumps(formatted_asset_data))
pipe.set(name='etf_list', value=json.dumps(formatted_etfs))
##

pipe.execute()

#################

print("Done!")

#################


# for el in assets:
#     ticker  = el['representative_ticker']
#     el_id   = el['id']

#     # List of id's
#     redis_conn.sadd('asset_ids', el_id)

#     # Hash asset-id => representative-ticker
#     redis_conn.hset('assets', el_id, ticker)

#     # Hash representative-ticker => asset-id
#     redis_conn.hset('tickers', ticker, el_id)


# for ticker in tickers:

#     # Mean return: VALUE
#     # Saves mean returns as a value under a key for each ticker
#     name = ''.join([ticker, ':mean_return'])
#     redis_conn.set(name=name, value=mean_returns[ticker])

#     # Standard-deviation: VALUE
#     # Saves standard deviation of returns as a value under a key for each ticker
#     name = ''.join([ticker, ':std_dev'])
#     redis_conn.set(name=name, value=std_dev_of_returns[ticker])

#     # Prices: HASH
#     # Saves all prices to a hash where the keys are the dates
#     name = ''.join([ticker, ':prices'])
#     for row in df.iterrows():
#         redis_conn.hset(name=name, key=row[0].date().strftime('%Y-%m-%d'), value=row[1][ticker])

#     # Correlations: HASH
#     # For a given ticker `A`, saves correlations for every other ticker as
#     # keys in the hash. Values against those keys are the correlations.
#     name = ''.join([ticker, ':correlations'])
#     temp = dict(correlation_matrix[ticker])
#     for i in temp.iteritems():
#         redis_conn.hset(name=name, key=i[0], value=i[1])

#     # Covariances: HASH
#     # For a given ticker `A`, saves covariances for every other ticker as
#     # keys in the hash. Values against those keys are the covariances.
#     name = ''.join([ticker, ':covariances'])
#     temp = dict(covariance_matrix[ticker])
#     for i in temp.iteritems():
#         redis_conn.hset(name=name, key=i[0], value=i[1])
