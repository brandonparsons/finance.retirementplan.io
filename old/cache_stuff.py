# Probably need pylibmc...

os.environ['MEMCACHE_SERVERS'] = os.environ.get('MEMCACHIER_SERVERS', '').replace(',', ';')
os.environ['MEMCACHE_USERNAME'] = os.environ.get('MEMCACHIER_USERNAME', '')
os.environ['MEMCACHE_PASSWORD'] = os.environ.get('MEMCACHIER_PASSWORD', '')

os.environ['CACHE_TYPE'] = os.environ.get('CACHE_TYPE', 'saslmemcached')

cache = Cache(app, config={
  'CACHE_TYPE': os.environ['CACHE_TYPE'],
  'CACHE_MEMCACHED_SERVERS':  [ os.environ['MEMCACHE_SERVERS'] ],
  'CACHE_MEMCACHED_USERNAME': os.environ['MEMCACHE_USERNAME'],
  'CACHE_MEMCACHED_PASSWORD': os.environ['MEMCACHE_PASSWORD']
})


os.environ['CACHE_TIMEOUT'] = os.environ.get('CACHE_TIMEOUT', None)
cache_timeout = int(os.environ['CACHE_TIMEOUT'])
@cache.memoize(timeout=cache_timeout)

@cache.memoize()
def cla(tickers, means, lB, uB, covars):
  # Expensive function.....


@app.route('/clear_cache', methods=["GET"])
def clear_cache_route():
  check_for_authorization()
  cache.clear()
  return jsonify({"message": "Done"})
