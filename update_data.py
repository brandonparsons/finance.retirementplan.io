import os
import redis
import functions

debug=False
write_csv=True
write_redis=True

# List of tickers you need in your analysis. Tickers matching Quandl data
# should be used here.
tickers = [
    'YAHOO/FUND_NAESX',
    'YAHOO/TSX_XLB_TO',
    'YAHOO/TSX_XSB_TO',
    'GOOG/AMEX_EWCS',
    'YAHOO/FUND_VFINX',
    'YAHOO/FUND_VUSTX'
]

# Retrieve historical data from Quandl and store it as a pandas DataFrame
# of daily close (or adjusted close) prices.
authtoken = os.getenv('QUANDL_TOKEN', '')
df = functions.get_prices(tickers=tickers, authtoken=authtoken, use_adjusted=True)

# Generate descriptive statistics for the datasets
returns, mean_returns, std_dev_of_returns, correlation_matrix, covariance_matrix = functions.get_stats_info(df)

# Print results
if debug:
    print 'Average daily returns: \n%s' % mean_returns
    print 'Standard-deviations: \n%s' % std_dev_of_returns
    print 'Correlations: \n%s' % correlation_matrix
    print 'Covariances: \n%s' % covariance_matrix

# Store relevant data in CSV's
if write_csv:
    functions.write_csv_files(df, returns, correlation_matrix, covariance_matrix)

# Store all relevant data in a Redis database
if write_redis:
    redis_url   = os.getenv('REDIS_URL', 'redis://localhost:6379/6')
    redis_conn  = redis.StrictRedis.from_url(redis_url) # host='localhost', port=6379, db=6)
    functions.write_redis_data(redis_conn, tickers, df, mean_returns, std_dev_of_returns, correlation_matrix, covariance_matrix)

print("Done!")
