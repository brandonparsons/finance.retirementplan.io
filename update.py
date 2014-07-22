import os
import json
import uuid
import math
import redis
import pandas as pd
import numpy as np

import lib.load_json_data as load_json_data
import lib.source_data as source_data
import lib.stats as stats


#################

print("Updating finance data in Redis....")

redis_url   = os.getenv('REDIS_URL')
if redis_url is None:
    raise KeyError("%s not present" % "REDIS_URL")
redis_conn  = redis.StrictRedis.from_url(redis_url)

# redis_conn = redis.StrictRedis(db=6) ## Development

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

# Get prices from external data source.
tickers = [ el['representative_ticker'] for el in assets ]
tickers.sort() # Sort as we are sorting means/covars/etc. Everything needs to be sorted so we treat things in the right order
prices = source_data.get_historical_prices(tickers) # Default option resamples the prices as monthly means - see source data file for why.

# Crunch statistics
mean_returns, std_dev_returns, covariance_matrix = stats.generate_stats(prices)

# Perform reverse portfolio optimization
# - FIXME: Updated Jul 18th- 2014. Need to update occasionally (along with returns). Some way to remember these need updating periodically?
# If swap later to real values (vs. nominal), can get long-term inflation expectations here: http://www.clevelandfed.org/research/data/inflation_expectations/
ANNUALIZED_LONG_TERM_RISK_FREE_RATE    = 0.025 # 10-year U.S. T-Bill - http://www.bloomberg.com/markets/rates-bonds/government-bonds/us/
MONTHLY_RISK_FREE_RATE      = math.pow( (1 + ANNUALIZED_LONG_TERM_RISK_FREE_RATE), (1.0/12.0) ) - 1

ANNUAL_MARKET_RISK_PREMIUM  = 0.0538 # http://pages.stern.nyu.edu/~%20adamodar/
MONTHLY_MARKET_RISK_PREMIUM = math.pow( (1 + ANNUAL_MARKET_RISK_PREMIUM), (1.0/12.0) ) - 1

market_portfolio_weights = pd.Series({ # FIXME: Copied from old spreadsheet, adjusted for tickers
    "EWC":      0.013,
    "VFINX":    0.10,
    "NAESX":    0.018,
    "EFA":      0.131,
    "EEM":      0.088,
    "XSB.TO":   0.013,
    "XLB":      0.001,
    "VFISX":    0.034,
    "VFITX":    0.027,
    "VUSTX":    0.013,
    "CSJ":      0.052,
    "CIU":      0.025,
    "LQD":      0.070,
    "BWX":      0.237,
    "IYR":      0.041,
    "XRE.TO":   0.005,
    "RWX":      0.115,
    "GSG":      0.019,
})

historical_risk_free_returns = source_data.get_tbill().pct_change()

reverse_optimized_monthly_returns = stats.reverse_portfolio_optimization(
    prices.pct_change()[:historical_risk_free_returns.tail(1).index[0]], # Cut prices off at end of tbills - tbills has less data
    historical_risk_free_returns[prices[0:1].index[0]:], # Start tbills at same start date as prices
    market_portfolio_weights,
    MONTHLY_MARKET_RISK_PREMIUM,
    MONTHLY_RISK_FREE_RATE)

#################

# Load and format the ETFs

etfs = load_json_data.get_etfs()

def uuid_for(ticker):
    encoded = ticker.encode('utf-8')
    return uuid.uuid5(uuid.NAMESPACE_DNS, encoded).hex

def add_id_to_etf(etf):
    etf['id'] = uuid_for(etf['ticker'])
    return etf

# Create formatted etf data to be returned from /etfs. Put it in an object
# as otherwise python won't want to load it.
formatted_etfs = {
    "etfs": [
        add_id_to_etf(etf) for etf in etfs
    ]
}

#################

# Save ETF latest quotes

etf_tickers = [ etf['ticker'] for etf in etfs ]
quotes = { "quotes": source_data.get_last_prices(etf_tickers) }

#################

# Before we store the data into redis, swap the tickers for asset IDs so that
# the whole algorithm is ticker-independent

# Build up the corresponding list of asset-ids to replace with
replacement_values = []
for ticker in tickers:
    relevant_asset_dict_index = next(index for (index, d) in enumerate(assets) if d['representative_ticker'] == ticker)
    asset_dict = assets[relevant_asset_dict_index]
    replacement_values.append(asset_dict['id'])

mean_returns.index              = replacement_values
std_dev_returns.index           = replacement_values
covariance_matrix.index         = replacement_values
covariance_matrix.columns       = replacement_values

# Re-sort the newly renamed dataframes/series
mean_returns    = mean_returns.sort_index()
std_dev_returns = std_dev_returns.sort_index()
covariance_matrix.sort_index(axis=0, inplace=True)
covariance_matrix.sort_index(axis=1, inplace=True)

cholesky_decomposition          = pd.DataFrame(np.linalg.cholesky(covariance_matrix))
cholesky_decomposition.index    = covariance_matrix.index
cholesky_decomposition.columns  = covariance_matrix.columns

#################

# Generate data for real estate and inflation

re   = source_data.get_real_estate()
infl = source_data.get_inflation()

re_mean, re_std_dev     = stats.stats_for_single_asset(re)
infl_mean, infl_std_dev = stats.stats_for_single_asset(infl)

re_obj = {
    "mean": re_mean,
    "std_dev": re_std_dev
}

infl_obj = {
    "mean": infl_mean,
    "std_dev": infl_std_dev
}

#################

# Save data to redis. Execute as multi to keep data consistency
pipe = redis_conn.pipeline()
pipe.multi()

##
pipe.set(name='mean_returns',               value=mean_returns.to_json())
pipe.set(name='reverse_optimized_returns',  value=reverse_optimized_monthly_returns.to_json())
pipe.set(name='std_dev_returns',            value=std_dev_returns.to_json())
pipe.set(name='covariance_matrix',          value=covariance_matrix.to_json())
pipe.set(name='cholesky_decomposition',     value=cholesky_decomposition.to_json())
##
pipe.set(name='asset_list', value=json.dumps(formatted_asset_data))
pipe.set(name='etf_list', value=json.dumps(formatted_etfs))
pipe.set(name='quotes', value=json.dumps(quotes))
pipe.set(name='inflation', value=json.dumps(infl_obj))
pipe.set(name='real_estate', value=json.dumps(re_obj))
##

pipe.execute()

#################

print("Done!")

#################

print("Clearing cache.....")
import requests

auth_token = os.environ.get('AUTH_TOKEN', 'abcd')
self_url = os.environ.get('SELF_URL', 'http://localhost:5000')
url = self_url + '/clear_cache'
r = requests.get(url, headers={'Authorization': auth_token})

print("Done!")

#################
