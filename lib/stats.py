import pandas as pd
import numpy as np

def generate_stats(dataframe):
    """
    Returns statistical information for a SET of securities - i.e. more than one.
    (Completes correlation/covariance matrices, etc.)
    :param dataframe: pandas DataFrame of asset prices
    :return: mean_returns, std_dev_of_returns, covariance_matrix
    """

    ## Calculate returns, mean and standard-deviation of each security's return ##
    returns = dataframe.pct_change()

    mean_returns = returns.mean()
    mean_returns = mean_returns.sort_index()

    std_dev_of_returns = returns.std()
    std_dev_of_returns = std_dev_of_returns.sort_index()

    ## Generate correlation and covariance matrices ##

    # roll_corr = pd.rolling_corr_pairwise(returns, window=5)
    # correlation_matrix  = returns.corr(method='pearson')  # other methods available: 'kendall', 'spearman'
    covariance_matrix = returns.cov()

    return mean_returns, std_dev_of_returns, covariance_matrix

def stats_for_single_asset(dataframe):
    """
    Returns statistical information for a SINGLE asset - does not attempt to
    obtain covariance / correlation matrices.
    :param dataframe: pandas DataFrame
    :return: mean_return, std_dev
    """
    returns = dataframe.pct_change()
    mean_return = returns.mean()
    std_dev = returns.std()

    return mean_return, std_dev

def reverse_portfolio_optimization(
    historical_return_data,
    historical_risk_free_returns,
    market_portfolio_weights,
    market_risk_premium,
    current_risk_free_rate):
    """
    Returns "market equilibrium" expected returns for a set of assets, based on
    the Black-Litterman Reverse Portfolio Optimization method.
    :param historical_return_data: pandas DataFrame of historical RETURNS (i.e. not prices) for the set of assets
    :param historical_risk_free_returns: pandas Series of historical RFR for the matching period
    :param market_portfolio_weights: pandas Series of market portfolio composition weights
    :param market_risk_premium: estimation of the current market risk premium
    :param current_risk_free_rate: estimation of the current risk-free rate

    :return: reverse_optimized_returns: pandas series of market equil. returns
    """

    # historical_return_data = pd.DataFrame({
        # "Cash": [0.06, 0.07, 0.06, 0.05],
        # "Bond": [0.02, -0.02, 0.07, 0.11],
        # "Stock": [-0.28, -0.02, 0.12, 0.16]
    # })
    # historical_risk_free_returns = historical_return_data['Cash']
    # market_portfolio_weights = pd.Series({
    #     "Cash": 0.1,
    #     "Bond": 0.6,
    #     "Stock": 0.3
    # })
    # market_risk_premium = 0.04
    # current_risk_free_rate = 0.05

    historical_return_data.sort()
    historical_mean_returns = historical_return_data.mean()
    historical_covariances = historical_return_data.cov()
    market_portfolio_weights.sort_index()

    ## 1: Convert to excess returns ##
    excess_returns = {}
    for asset, historical_returns in historical_return_data.iteritems():
        excess_returns[asset] = [ (ret - historical_risk_free_returns[index] + current_risk_free_rate) for index, ret in enumerate(historical_returns) ]
    excess_returns = pd.DataFrame(excess_returns)

    ## 2: Get covariances ##
    excess_return_covariances = excess_returns.cov()

    ## 3: Get beta ##
    # A) Covariance of assets with mkt portfolio
    covariances = {}
    for asset in excess_return_covariances:
        covars = excess_return_covariances[asset]
        covariances[asset] = np.dot(market_portfolio_weights, covars)
    covariances = pd.Series(covariances)

    # B) Variance of mkt portfolio
    var_mkt_port = np.dot(covariances, market_portfolio_weights)

    # c) Calculate Betas
    betas = covariances / var_mkt_port

    ## 4: Calculate returns via beta ##
    reverse_optimized_returns = betas * market_risk_premium + current_risk_free_rate

    return reverse_optimized_returns
