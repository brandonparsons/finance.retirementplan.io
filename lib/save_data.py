import os
import redis
import pandas

def write_csv_files(df, returns, correlation_matrix, covariance_matrix):
    # Store all data as flat csv files. Whenever you run this function, the output
    # files will be overwritten.
    this_dir    = os.path.dirname(__file__)
    csv_dir     = os.path.join(this_dir, os.pardir, 'csv')

    df.to_csv( os.path.join(csv_dir, 'prices.csv'), header=True, index=True, index_label='Date', sep=',')
    returns.to_csv( os.path.join(csv_dir, 'returns.csv'), header=True, index=True, index_label='Date', sep=',')
    correlation_matrix.to_csv( os.path.join(csv_dir, 'correlation_matrix.csv'), header=True, index=True, sep=',')
    covariance_matrix.to_csv( os.path.join(csv_dir, 'covariance_matrix.csv'), header=True, index=True, sep=',')

def write_redis_data(redis_conn, mean_returns, std_dev_of_returns, covariance_matrix):
    # Store relevant data in a Redis database
    # Eliminated arguments (as not currently using):
    # - tickers
    # - df

    redis_conn.set(name='mean_returns', value=mean_returns.to_json())
    redis_conn.set(name='std_dev_returns', value=std_dev_of_returns.to_json())
    redis_conn.set(name='covariance_matrix', value=covariance_matrix.to_json())

    # # Iterate through each ticker and save its data into the db
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
