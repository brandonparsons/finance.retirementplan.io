import os
import redis

from lib.inflation    import inflation_json                   as inflation_json
from lib.real_estate  import real_estate_json                 as real_estate_json
from lib.etfs         import etf_json                         as etf_json
from lib.etfs         import quotes_json                      as quotes_json
from lib.assets       import asset_json                       as asset_json
from lib.assets       import mean_return_json                 as mean_return_json
from lib.assets       import reverse_optimized_returns_json   as reverse_optimized_returns_json
from lib.assets       import std_dev_returns_json             as std_dev_returns_json
from lib.assets       import covariance_matrix_json           as covariance_matrix_json
from lib.assets       import cholesky_decomposition_json      as cholesky_decomposition_json
from lib.cache        import clear                            as clear_cache


#################

def _get_redis_connection():
    redis_url   = os.getenv('REDIS_URL')
    if redis_url is None:
        raise KeyError("%s not present" % "REDIS_URL")
    r  = redis.StrictRedis.from_url(redis_url)
    # r = redis.StrictRedis(db=6) ## Development
    return r

#################


print("Updating finance data in Redis....")

pipe = _get_redis_connection().pipeline()

pipe.multi() # Execute as multi so all data refreshed at once

pipe.set(name='asset_list',                 value=asset_json())
pipe.set(name='etf_list',                   value=etf_json())
pipe.set(name='inflation',                  value=inflation_json())
pipe.set(name='real_estate',                value=real_estate_json())
pipe.set(name='quotes',                     value=quotes_json())
pipe.set(name='mean_returns',               value=mean_return_json())
pipe.set(name='reverse_optimized_returns',  value=reverse_optimized_returns_json())
pipe.set(name='std_dev_returns',            value=std_dev_returns_json())
pipe.set(name='covariance_matrix',          value=covariance_matrix_json())
pipe.set(name='cholesky_decomposition',     value=cholesky_decomposition_json())

pipe.execute()

#################

print("Clearing cache.....")
clear_cache()

#################

print("Done!")
