# ----------------------------------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------------------------------
import redis
pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=pool)

# Get all prices for YAHOO/TSX_XSB_TO
r.hgetall(''.join(['YAHOO/TSX_XSB_TO', ':prices']))

# Get correlation value of YAHOO/TSX_XSB_TO to YAHOO/FUND_VUSTX
float(r.hget(name='YAHOO/TSX_XSB_TO:correlations', key='YAHOO/FUND_VUSTX'))

# Get covariance value of YAHOO/TSX_XSB_TO to YAHOO/FUND_VUSTX
float(r.hget(name='YAHOO/TSX_XSB_TO:covariances', key='YAHOO/FUND_VUSTX'))

# Get correlation values of YAHOO/TSX_XSB_TO
r.hgetall(name='YAHOO/TSX_XSB_TO:correlations')

# Get covariance values of YAHOO/TSX_XSB_TO
r.hgetall(name='YAHOO/TSX_XSB_TO:covariances')

def load_prices(r, name):
    """
    Parser function to load prices from Redis database.

    :param r: Redis connection
    :param name: name of the series stored in the Redis database
    :return: a pandas DataFrame
    """
    data = r.hgetall(name)
    data = pd.DataFrame(data=map(lambda x: float(x), data.values()),
                        index=map(lambda x: pd.Timestamp(x, '%Y-%m-%d'), data.keys()))
    data = data.sort().dropna()
    data.columns = [name]
    data.index.names = ['Date']
    return data
load_prices(r=r, name='YAHOO/TSX_XSB_TO:prices')
