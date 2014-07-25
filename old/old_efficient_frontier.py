import math
import numpy as np
from lib.CLA import CLA

number_of_points = 30

#######

def lower_bounds(length):
    return np.zeros(length).reshape(length, 1)

def upper_bounds(length):
    return np.ones(length).reshape(length, 1)

def format_mean_returns_dataframe(df, length):
    # # No longer need to sort the index - already doing that
    # return df.sort_index().values.reshape(length, 1)
    return df.values.reshape(length, 1)

def format_covars_dataframe(df):
    # # No longer need to sort the index - already doing that
    # return df.sort(axis=0).sort(axis=1).values
    return df.values

def format_resulting_weights(weights, asset_ids):
    formatted_weights = [ entry[0] for entry in weights ]

    allocation = {}
    for i, weight in enumerate(formatted_weights):
        allocation[asset_ids[i]] = weight

    return allocation

#######

def annual_nominal_return(monthly_mean_return):
    return math.pow((1 + monthly_mean_return), 12) - 1 # + 0.02 ## using nominal historical returns

def annual_std_dev(monthly_std_dev):
    return monthly_std_dev * math.sqrt(12)

#######

def efficient_frontier(asset_ids, mean_returns, covariance_matrix):
    # Format data

    number_of_asset_ids = mean_returns.size
    means   = format_mean_returns_dataframe(mean_returns, number_of_asset_ids)
    covars  = format_covars_dataframe(covariance_matrix)
    lB      = lower_bounds(number_of_asset_ids)
    uB      = upper_bounds(number_of_asset_ids)

    # Solve critical line algorithm
    cla = CLA(means, covars, lB, uB)
    cla.solve()

    # Get turning point portfolios
    mu,sigma,weights = cla.efFrontier(number_of_points)

    # Format turning point portfolios
    formatted_weights = []
    for entry in weights:
        flattened = [item for sublist in entry.tolist() for item in sublist]
        formatted_weights.append(flattened)

    portfolios = []

    for index, portfolio_allocation in enumerate(formatted_weights):
        obj = {}
        monthly_mean_return = mu[index]
        monthly_std_dev     = sigma[index]

        obj["statistics"] = {
            "mean_return": monthly_mean_return,
            "std_dev": monthly_std_dev,
            "annual_nominal_return": annual_nominal_return(monthly_mean_return),
            "annual_std_dev": annual_std_dev(monthly_std_dev)
        }

        allocation = {}
        for i, weight in enumerate(portfolio_allocation):
          allocation[asset_ids[i]] = weight
        obj["allocation"]  = allocation

        portfolios.append(obj)

    # On quick inspection of the algorithm, the minimum variance and maximum
    # Sharpe Ratio portfolios appear to be pulled from the results - i.e. they
    # are not NEW portfolios and don't need to be separately included unless
    # you want to mark them for some reason.  REMOVING from the response.

    # # Add the minimum variance portfolio
    # var, weights = cla.getMinVar()
    # allocation = format_resulting_weights(weights, asset_ids)
    # monthly_mean_return = np.dot(weights.T, means)[0,0]
    # monthly_std_dev     = var[0,0]

    # min_var_port = {
    #     "allocation": allocation,
    #     "statistics": {
    #         "mean_return": monthly_mean_return,
    #         "std_dev": monthly_std_dev,
    #         "annual_nominal_return": annual_nominal_return(monthly_mean_return),
    #         "annual_std_dev": annual_std_dev(monthly_std_dev)
    #     }
    # }

    # # Add the maximum sharpe ratio portfolio
    # sr, weights = cla.getMaxSR()
    # allocation = format_resulting_weights(weights, asset_ids)
    # monthly_mean_return = np.dot(weights.T, means)[0,0]
    # monthly_std_dev     = np.dot(weights.T, np.dot(covars, weights))[0,0]**0.5

    # max_sr_port = {
    #     "allocation": allocation,
    #     "statistics": {
    #         "mean_return": monthly_mean_return,
    #         "std_dev": monthly_std_dev,
    #         "annual_nominal_return": annual_nominal_return(monthly_mean_return),
    #         "annual_std_dev": annual_std_dev(monthly_std_dev)
    #     }
    # }

    # Return results
    return {
      "portfolios": portfolios,
      # "minimum_variance_portfolio": min_var_port,
      # "maximum_sharpe_ratio_portfolio": max_sr_port
    }
