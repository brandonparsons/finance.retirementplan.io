import numpy as np
from lib.CLA import CLA

number_of_points = 30

def lower_bounds(length):
    return np.zeros(length).reshape(length, 1)

def upper_bounds(length):
    return np.ones(length).reshape(length, 1)

def format_mean_returns_dataframe(df, length):
    return df.sort_index().values.reshape(length, 1)

def format_covars_dataframe(df):
    return df.sort(axis=0).sort(axis=1).values

def format_resulting_weights(weights, tickers):
    formatted_weights = [ entry[0] for entry in weights ]

    allocations = {}
    for i, weight in enumerate(formatted_weights):
        allocations[tickers[i]] = weight

    return allocations

#######

def efficient_frontier(tickers, mean_returns, covariance_matrix):
    # Format data
    number_of_tickers = mean_returns.size
    means   = format_mean_returns_dataframe(mean_returns, number_of_tickers)
    covars  = format_covars_dataframe(covariance_matrix)
    lB      = lower_bounds(number_of_tickers)
    uB      = upper_bounds(number_of_tickers)

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

    for index, allocation in enumerate(formatted_weights):
        obj = {}
        obj['mu'] = mu[index]
        obj['sigma'] = sigma[index]

        allocations = {}
        for i, weight in enumerate(allocation):
          allocations[tickers[i]] = weight

        obj['allocations']  = allocations

        portfolios.append(obj)

    # Add the minimum variance portfolio
    var, weights = cla.getMinVar()
    allocations = format_resulting_weights(weights, tickers)

    min_var_port = {
        "mu": np.dot(weights.T, means)[0,0],
        "sigma": var[0,0],
        "allocations": allocations
    }

    # Add the maximum sharpe ratio portfolio
    sr, weights = cla.getMaxSR()
    allocations = format_resulting_weights(weights, tickers)

    max_sr_port = {
        "mu": np.dot(weights.T, means)[0,0],
        "sigma": np.dot(weights.T, np.dot(covars, weights))[0,0]**0.5,
        "allocations": allocations
    }

    # import pdb; pdb.set_trace()

    # Return results
    return {
      "portfolios": portfolios,
      "minimum_variance_portfolio": min_var_port,
      "maximum_sharpe_ratio_portfolio": max_sr_port
    }
