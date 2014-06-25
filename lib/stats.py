import pandas

def generate_stats(dataframe):
    """
    :param dataframe: pandas DataFrame
    :return: mean_returns, covariance_matrix
    """

    # Calculate returns, mean and standard-deviation of each security's return
    returns             = dataframe.pct_change()
    mean_returns        = returns.mean()
    std_dev_of_returns  = returns.std()

    # Generate correlation and covariance matrices
    correlation_matrix  = returns.corr(method='pearson')  # other methods available: 'kendall', 'spearman'
    covariance_matrix   = returns.cov()
    # roll_corr = pd.rolling_corr_pairwise(returns, window=5)

    # Only returning means & covars for now (that's all we're using at the moment)
    return mean_returns, std_dev_of_returns, covariance_matrix
