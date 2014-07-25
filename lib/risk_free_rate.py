###########
# IMPORTS #
###########

import math


####################
# MODULE VARIABLES #
####################

## - FIXME: Updated Jul 18th- 2014. Need to update occasionally....Figure out way to remember or set cron job? Scrape?

ANNUALIZED_LONG_TERM_RISK_FREE_RATE = 0.025 # 10-year U.S. T-Bill - http://www.bloomberg.com/markets/rates-bonds/government-bonds/us/
ANNUAL_MARKET_RISK_PREMIUM = 0.0538 # http://pages.stern.nyu.edu/~%20adamodar/

# If swap later to real values (vs. nominal), can get long-term inflation expectations here: http://www.clevelandfed.org/research/data/inflation_expectations/


##############
# PUBLIC API #
##############

def monthly_risk_free_rate():
    return math.pow( (1 + ANNUALIZED_LONG_TERM_RISK_FREE_RATE), (1.0/12.0) ) - 1

def monthly_market_risk_premium():
    return math.pow( (1 + ANNUAL_MARKET_RISK_PREMIUM), (1.0/12.0) ) - 1
