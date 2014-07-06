import json
import redis
import pandas as pd
import numpy as np

r = redis.StrictRedis(db=6)

json = r.get('covariance_matrix')
df   = pd.io.json.read_json(json)

arr = np.array([
  [25, 15, -5],
  [15, 18, 0],
  [-5, 0, 11],
])

cholesky = np.linalg.cholesky(arr)
