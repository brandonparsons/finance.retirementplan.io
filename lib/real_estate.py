###########
# IMPORTS #
###########

from __future__ import absolute_import

import json
import Quandl


##############
# PUBLIC API #
##############

def real_estate_json():
    return json.dumps(_json_data_obj())


###############
# PRIVATE API #
###############

def _source_data(trim_start="2007-10-01"):
    # Trimming to 2007-10-01 to be on ~ the same timescale as have data for all
    # other securities.
    df = Quandl.get("SANDP/HPI_COMPOSITE10_SA", trim_start=trim_start, collapse="monthly")
    return df['Index']

def _json_data_obj():
    returns = _source_data().pct_change()
    return {
        "mean":     returns.mean(),
        "std_dev":  returns.std(),
    }
