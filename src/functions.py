import os
import pandas as pd
import Quandl
import redis

def get_prices(tickers, authtoken, use_adjusted=True):
    """
    :param tickers: list of tickers as strings
    :param authtoken: your authtoken
    :param use_adjusted: boolean, whether to use the adjusted close if available or not
    :return: pandas DataFrame of asset prices
    """
    df = pd.DataFrame()
    for ticker in tickers:
        data = Quandl.get(ticker, authtoken=authtoken)
        if use_adjusted:
            if 'Adjusted Close' in data.columns:
                data = data[['Adjusted Close']]
            else:
                data = data[['Close']]
        else:
            data = data[['Close']]
        data.columns = [ticker]
        df = pd.merge(df, data, left_index=True, right_index=True, how='outer')
    return df

def get_stats_info(df):
    # Fill missing values by linear interpolation
    df = df.interpolate()

    # Drop rows with unavailable data. It will line up the starting date of all
    # of the tickers. For correlations & covariances it would be better to use
    # as much data as possible, but the std_dev & mean really should be over
    # the same time period.
    df.dropna()

    # If you want to work with weekly or monthly prices:
    # df = df.resample('W')  # 'W' for weekly, 'M' for monthly

    # Calculate returns, mean and standard-deviation of each security's return
    returns             = df.pct_change()
    mean_returns        = returns.mean()
    std_dev_of_returns  = returns.std()

    # Generate correlation and covariance matrices
    correlation_matrix  = returns.corr(method='pearson')  # other methods available: 'kendall', 'spearman'
    covariance_matrix   = returns.cov()
    # roll_corr = pd.rolling_corr_pairwise(returns, window=5)

    return returns, mean_returns, std_dev_of_returns, correlation_matrix, covariance_matrix

def write_csv_files(df, returns, correlation_matrix, covariance_matrix):
    # Store all data as flat csv files. Whenever you run this script, the output
    # files will be overwritten.
    this_dir = os.path.dirname(__file__)
    csv_dir = os.path.join(this_dir, os.pardir, 'csv')

    df.to_csv( os.path.join(csv_dir, 'prices.csv'), header=True, index=True, index_label='Date', sep=',')
    returns.to_csv( os.path.join(csv_dir, 'returns.csv'), header=True, index=True, index_label='Date', sep=',')
    correlation_matrix.to_csv( os.path.join(csv_dir, 'correlation_matrix.csv'), header=True, index=True, sep=',')
    covariance_matrix.to_csv( os.path.join(csv_dir, 'covariance_matrix.csv'), header=True, index=True, sep=',')

def write_redis_data(tickers, df, mean_returns, std_dev_of_returns, correlation_matrix, covariance_matrix):
    # Store all data in a Redis database
    pool = redis.ConnectionPool(host='localhost', port=6379, db=6)
    r = redis.Redis(connection_pool=pool)

    # Iterate through each ticker and save its data into the db
    for ticker in tickers:

        # Prices: HASH
        name = ''.join([ticker, ':prices'])
        for row in df.iterrows():
            r.hset(name=name, key=row[0].date().strftime('%Y-%m-%d'), value=row[1][ticker])

        # Mean return: VALUE
        name = ''.join([ticker, ':mean_return'])
        r.set(name=name, value=mean_returns[ticker])

        # Standard-deviation: VALUE
        name = ''.join([ticker, ':std_dev'])
        r.set(name=name, value=std_dev_of_returns[ticker])

        # Correlations: HASH
        name = ''.join([ticker, ':correlations'])
        temp = dict(correlation_matrix[ticker])
        for i in temp.iteritems():
            r.hset(name=name, key=i[0], value=i[1])

        # Covariances: HASH
        name = ''.join([ticker, ':covariances'])
        temp = dict(covariance_matrix[ticker])
        for i in temp.iteritems():
            r.hset(name=name, key=i[0], value=i[1])
