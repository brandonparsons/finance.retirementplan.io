# Python Web Service for Critical Line Algorithm #

## Instructions ##

### Dependencies ###

1. Python (virtualenv/pip)
2. Redis

### To run server ###

1. `source bin/venv/activate`
2. `pip install -r requirements.txt`
3. `foreman start`

### Once finished ###

1. `http GET localhost:5000/clear_cache Authorization:abcd` (If have caching set up)
2. `deactivate`

## Example POST Request ##

**Use a different Authorization header if you change it**

```
# Uses httpie

http POST 'http://localhost:5000/calc' asset_ids:='["INTL-STOCK", "COMMODITIES", "US-LGCAP-STOCK"]' 'Authorization: abcd'

```
