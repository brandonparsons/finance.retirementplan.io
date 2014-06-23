import os
import functions

debug=False
write_csv=True
write_redis=True

# List of tickers you need in your analysis. Tickers matching Quandl data should be used here.
tickers = [
    'YAHOO/FUND_NAESX',
    'YAHOO/TSX_XLB_TO',
    'YAHOO/TSX_XSB_TO',
    'GOOG/AMEX_EWCS',
    'YAHOO/FUND_VFINX',
    'YAHOO/FUND_VUSTX'
]

# Put your Quandl authtoken here:
authtoken = os.getenv('QUANDL_TOKEN', '')

# Retrieve historical data from Quandl and store it as a pandas DataFrame
# of daily close (or adjusted close) prices.
df = functions.get_prices(tickers=tickers, authtoken=authtoken, use_adjusted=True)

returns, mean_returns, std_dev_of_returns, correlation_matrix, covariance_matrix = functions.get_stats_info(df)

if debug:
    print 'Average daily returns: \n%s' % mean_returns
    print 'Standard-deviations: \n%s' % std_dev_of_returns
    print 'Correlations: \n%s' % correlation_matrix
    print 'Covariances: \n%s' % covariance_matrix

if write_csv:
    functions.write_csv_files(df, returns, correlation_matrix, covariance_matrix)

if write_redis:
    functions.write_redis_data(tickers, df, mean_returns, std_dev_of_returns, correlation_matrix, covariance_matrix)

print("Done!")
