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
