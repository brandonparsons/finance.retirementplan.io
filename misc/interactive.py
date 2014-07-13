import json
import redis
import pandas as pd
import numpy as np

r = redis.StrictRedis(db=6)

json = r.get('covariance_matrix')
df   = pd.io.json.read_json(json)
