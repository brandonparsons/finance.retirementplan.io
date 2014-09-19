###########
# IMPORTS #
###########

from __future__ import absolute_import

import math
from numpy import linspace, ones, dot, array
import scipy, scipy.optimize

from . import risk_free_rate


####################
# MODULE VARIABLES #
####################

NUMBER_PORTFOLIOS_TO_GENERATE = 20


##############
# PUBLIC API #
##############

def efficient_frontier(asset_ids, asset_returns, historical_returns, covariance_matrix):
    """
    Generates and formats an efficient frontier for a given set of asset ids,
    and their corresponding mean returns and covariances. ID's and the columns/indexes of means/covars are expected to match.
    :param asset_ids: array of asset ID's (e.g. INTL-STOCK)
    :param asset_returns: numpy array of the relevant returns corresponding to passed in asset_ids - typically the market implied returns
    :param historical_returns: numpy array of the historical mean returns corresponding to passed in asset_ids
    :param covariance_matrix: numpy matrix of the covariances corresponding to passed in asset_ids
    """

    # Generate the frontier
    rfr      = risk_free_rate.monthly_risk_free_rate()
    frontier = _solve_frontier(asset_returns, covariance_matrix, rfr)

    # Format the frontier, pass in the historical returns so that historical portfolio returns can be calculated
    formatted = _format_frontier(frontier, asset_ids, historical_returns)

    # Sort & cull
    culled = _sort_and_cull_frontier(formatted)

    return { "portfolios": culled }


###############
# PRIVATE API #
###############

def _sort_and_cull_frontier(frontier):
    # Frontier needs to be sorted by increasing level of risk prior to cull algorithm
    frontier.sort(key=lambda elem: elem['statistics']['std_dev'] )

    culled_frontier = []
    last_return = -999999

    for portfolio in frontier:
        if portfolio['statistics']['mean_return'] > last_return:
            last_return = portfolio['statistics']['mean_return']
            culled_frontier.append(portfolio)

    return culled_frontier

def _format_frontier(frontier, asset_ids, historical_returns):
    frontier_means      = frontier[0]
    frontier_variances  = frontier[1]
    frontier_weights    = frontier[2]
    formatted_frontier  = []
    for index, portfolio_allocation in enumerate(frontier_weights):
        rounded_portfolio_allocation    = [round(asset_weight, 4) for asset_weight in portfolio_allocation]
        this_portfolios_mean            = frontier_means[index]
        this_portfolios_std_dev         = math.pow(frontier_variances[index], 0.5)
        formatted_frontier.append({
            "allocation": dict(zip(asset_ids, rounded_portfolio_allocation)),
            "statistics": {
                "mean_return":              this_portfolios_mean,
                "std_dev":                  this_portfolios_std_dev,
                "annual_nominal_return":    _annual_nominal_return(this_portfolios_mean),
                "annual_std_dev":           _annual_std_dev(this_portfolios_std_dev),
                "annual_alternate_return":  _annual_nominal_return(_port_mean(portfolio_allocation, historical_returns))
            }
        })
    return formatted_frontier

def _annual_nominal_return(monthly_mean_return, nominal=True):
    """
    Converts a monthly mean return (nominal default) to an annualized nominal return
    """
    annualized = math.pow((1 + monthly_mean_return), 12) - 1
    if not nominal:
        annualized += 0.02 # Assume 2% inflation ## This is NOT getting called by default
    return annualized

def _annual_std_dev(monthly_std_dev):
    """
    Converts a monthly standard deviation to an annualized value
    """
    return monthly_std_dev * math.sqrt(12)

def _port_mean(weights, means):
    """
    Calculates portfolio mean return
    :param weights: numpy array of asset weights
    :param means: numpy array of asset mean returns
    """
    return sum(means * weights)

def _port_var(weights, covars):
    """
    Calculates portfolio variance of returns
    :param weights: numpy array of asset weights
    :param covars: numpy matrix of asset covariances
    """
    return dot(dot(weights, covars), weights)

# Combination of the two functions above - mean and variance of returns calculation
def _port_mean_var(weights, means, covars):
    """
    Combination function - returns portfolio mean & variance
    :param weights: numpy array of asset weights
    :param means: numpy array of asset mean returns
    :param covars: numpy matrix of asset covariances
    """
    return _port_mean(weights, means), _port_var(weights, covars)

def _solve_frontier(R, C, rf):
    """
    Given risk-free rate, assets returns and covariances, this function calculates
    mean-variance frontier and returns its [x,y] points in two arrays.
    Source: https://code.google.com/p/quantandfinancial/ GNU GPL v3
    Not modified except for underscores in front of method names.
    :param R: numpy array of asset mean returns
    :param C: numpy array of asset covariances
    :param rf: risk-free rate
    """
    def fitness(W, R, C, r):
        # For given level of return r, find weights which minimizes portfolio variance.
        mean, var = _port_mean_var(W, R, C)
        # Big penalty for not meeting stated portfolio return effectively serves as optimization constraint
        penalty = 50*abs(mean-r)
        return var + penalty
    frontier_mean, frontier_var, frontier_weights = [], [], []
    n = len(R) # Number of assets in the portfolio
    for r in linspace(min(R), max(R), num=NUMBER_PORTFOLIOS_TO_GENERATE): # Iterate through the range of returns on Y axis
        W = ones([n])/n  # Start optimization with equal weights
        b_ = [(0,1) for i in range(n)]
        c_ = ({'type':'eq', 'fun': lambda W: sum(W)-1. })
        optimized = scipy.optimize.minimize(fitness, W, (R, C, r), method='SLSQP', constraints=c_, bounds=b_)
        if not optimized.success:
            raise BaseException(optimized.message)
        # Add point to the min-var frontier [x,y] = [optimized.x, r]
        frontier_mean.append(r) # return
        frontier_var.append(_port_var(optimized.x, C)) # min-variance based on optimized weights
        frontier_weights.append(optimized.x)
    return array(frontier_mean), array(frontier_var), frontier_weights
