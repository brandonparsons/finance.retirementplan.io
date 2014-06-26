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
