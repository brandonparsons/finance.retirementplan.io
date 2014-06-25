import os
import yaml
import redis

import lib.load_json_data as load_json_data
import lib.source_data as source_data
import lib.stats as stats
import lib.save_data as save_data

print("Updating securities data in Redis....")

# Loads the overall assets/securities, not the individual etfs
assets  = load_json_data.get_assets()
tickers = [ el['representative_ticker'] for el in assets ]

# Get prices from external data source
prices = source_data.get_prices(tickers)

# Crunch statistics
mean_returns, std_dev_returns, covariance_matrix = stats.generate_stats(prices)

# Save data to redis
redis_url   = os.getenv('REDIS_URL')
redis_conn  = redis.StrictRedis.from_url(redis_url)
save_data.write_redis_data(redis_conn, mean_returns, std_dev_returns, covariance_matrix)

print("Done!")
