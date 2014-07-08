def generate_stats(dataframe):
    """
    :param dataframe: pandas DataFrame
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
    correlation_matrix  = returns.corr(method='pearson')  # other methods available: 'kendall', 'spearman'
    covariance_matrix   = returns.cov()

    return mean_returns, std_dev_of_returns, covariance_matrix
