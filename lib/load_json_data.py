import os
import json

this_dir = os.path.dirname(__file__)
json_dir = os.path.join(this_dir, os.pardir, 'config')

def get_assets():
    with open(os.path.join(json_dir, 'assets.json')) as data_file:
        data = json.load(data_file)
    return data

def get_etfs():
    with open(os.path.join(json_dir, 'etfs.json')) as data_file:
        data = json.load(data_file)
    return data
