###########
# IMPORTS #
###########

import os
import json
import math
import datetime
import pandas           as pd
import pandas.io.data   as web
import numpy            as np
import Quandl


####################
# MODULE VARIABLES #
####################

monthly_prices = None

## - FIXME: Updated Jul 18th- 2014. Need to update occasionally....Figure out way
## to remember or set cron job? Scrape?
ANNUALIZED_LONG_TERM_RISK_FREE_RATE = 0.025 # 10-year U.S. T-Bill - http://www.bloomberg.com/markets/rates-bonds/government-bonds/us/
ANNUAL_MARKET_RISK_PREMIUM = 0.0538 # http://pages.stern.nyu.edu/~%20adamodar/
# If swap later to real values (vs. nominal), can get long-term inflation
# expectations here: http://www.clevelandfed.org/research/data/inflation_expectations/


##############
# PUBLIC API #
##############

def asset_json():
    return json.dumps(_formatted_asset_data())

def mean_return_json():
    return _mean_returns().to_json()

def reverse_optimized_returns_json():
    return _reverse_optimized_returns().to_json()

def std_dev_returns_json():
    return _std_dev_returns().to_json()

def covariance_matrix_json():
    return _covariance_matrix().to_json()

def cholesky_decomposition_json():
    return _cholesky_decomposition().to_json()


###############
# PRIVATE API #
###############

def _formatted_asset_data():
    # Create formatted asset data to be returned from /assets. Put it in an
    # object as otherwise python won't want to load it.
    def asset_without_representative_ticker(asset):
        tmp = asset.copy()
        del tmp['representative_ticker']
        return tmp

    return {
        "assets": [
            asset_without_representative_ticker(el) for el in _assets()
        ]
    }

def _get_selected_tickers():
    selected_tickers = [ el['representative_ticker'] for el in _assets() ]
    selected_tickers.sort() # Sort as we are sorting means/covars/etc. Everything needs to be sorted so we treat things in the right order
    return selected_tickers

def _mean_returns():
    means           = _monthly_returns().mean()
    means           = means.sort_index()
    means.index     = _replacement_values_for_tickers()
    means           = means.sort_index()
    return means

def _std_dev_returns():
    stds         = _monthly_returns().std()
    stds         = stds.sort_index()
    stds.index   = _replacement_values_for_tickers()
    stds         = stds.sort_index()
    return stds

# def _correlation_matrix():
    # roll_corr = pd.rolling_corr_pairwise(_monthly_returns(), window=5)
    # corr_mat  = _monthly_returns().corr(method='pearson')  # other methods available: 'kendall', 'spearman'

def _covariance_matrix():
    covs           = _monthly_returns().cov()
    covs.index     = _replacement_values_for_tickers()
    covs.columns   = _replacement_values_for_tickers()
    covs.sort_index(axis=0, inplace=True)
    covs.sort_index(axis=1, inplace=True)
    return covs

def _cholesky_decomposition():
    covars              = _covariance_matrix()
    cholesky            = pd.DataFrame(np.linalg.cholesky(covars))
    cholesky.index      = covars.index
    cholesky.columns    = covars.columns
    return cholesky

def _replacement_values_for_tickers():
    # Before we return the data for storage, swap the tickers for asset IDs so that
    # everything outside of this file is **ticker-independent**
    # _get_selected_tickers() is sorted
    assets_list = _assets()
    replacement_values = []
    for ticker in _get_selected_tickers():
        relevant_asset_dict_index = next(index for (index, d) in enumerate(assets_list) if d['representative_ticker'] == ticker)
        asset_dict = assets_list[relevant_asset_dict_index]
        replacement_values.append(asset_dict['id'])
    return replacement_values

def _get_historical_prices(tickers):
    """
    Obtains resampled historical adjusted close prices for tickers.
    :param tickers: list of tickers as strings
    :return: pandas DataFrame of asset prices
    """
    # Defaults (not going to add complexity to args list)
    use_adjusted        = True
    resample_monthly    = True
    start               = datetime.datetime(2000, 1, 1).date()
    end                 = datetime.date.today()
    data_source         = 'yahoo' # 'google'

    def getWebTickerData(ticker):
        """
        :param ticker: string, Yahoo finance ticker
        :return: pandas DataFrame of ticker Close data
        """
        return web.DataReader(ticker, data_source, start, end)

    # def getQuandlTickerData(ticker):
        # authtoken = os.getenv('QUANDL_TOKEN', '')
        # data = Quandl.get(ticker, authtoken=authtoken, transformation=transformation)
        # return data

    df = pd.DataFrame()

    for ticker in tickers:
        data = getWebTickerData(ticker)
        if use_adjusted:
            if 'Adjusted Close' in data.columns:
                data = data[['Adjusted Close']]
            else:
                data = data[['Close']]
        else:
            data = data[['Close']]
        data.columns = [ticker]
        df = pd.merge(df, data, left_index=True, right_index=True, how='outer')

    # Fill missing values by linear interpolation
    df = df.interpolate()

    # Drop rows with unavailable data. It will line up the starting date of all
    # of the tickers. For correlations & covariances it would be better to use
    # as much data as possible, but the std_dev & mean really should be over
    # the same time period.
    df = df.dropna()

    # Resample to monthly:
    # - We only have monthly data for real estate index (for simulation - not ETFs)
    # - Monthly mean/variance is statistically more relevant for long-term investors (smooths short-term volatility)
    # - T-Bill returns used in reverse portfolio optimization only have monthly/annual values - timeframes need to line up
    # - Doing monthly monte carlo simulations weekly gets to resource-intensive
    if resample_monthly:
        df = df.resample('M', how='mean')

    return df

def _get_tbill(trim_start="2000-01-31"):
    """
    Obtains monthly historical TBill returns from the U.S. Treasury, which will
    be assumed to be a good proxy for the "Risk Free Rate"
    :return: pandas DataFrame of TBill data
    """
    df = Quandl.get("WREN/W10", trim_start=trim_start, collapse="monthly")
    return df['Value']

def _reverse_optimized_returns():
    # Perform reverse portfolio optimization

    monthly_risk_free_rate      = math.pow( (1 + ANNUALIZED_LONG_TERM_RISK_FREE_RATE), (1.0/12.0) ) - 1
    monthly_market_risk_premium = math.pow( (1 + ANNUAL_MARKET_RISK_PREMIUM), (1.0/12.0) ) - 1

    # Copied from old spreadsheet, adjusted for tickers
    # FIXME: These need updating at some point, and on semi-regular basis (1-2x per year?)
    market_portfolio_weights = pd.Series({
        "EWC":      0.013,
        "VFINX":    0.10,
        "NAESX":    0.018,
        "EFA":      0.131,
        "EEM":      0.088,
        "XSB.TO":   0.013,
        "XLB":      0.001,
        "VFISX":    0.034,
        "VFITX":    0.027,
        "VUSTX":    0.013,
        "CSJ":      0.052,
        "CIU":      0.025,
        "LQD":      0.070,
        "BWX":      0.237,
        "IYR":      0.041,
        "XRE.TO":   0.005,
        "RWX":      0.115,
        "GSG":      0.019,
    })

    historical_risk_free_returns = _get_tbill().pct_change()

    # Cut prices off at end of tbills - tbills has less data
    relevant_prices = _monthly_returns()[:historical_risk_free_returns.tail(1).index[0]]

    # Start tbills at same start date as prices
    relevant_historical_returns = historical_risk_free_returns[_monthly_returns()[0:1].index[0]:]

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

    optimized_returns = reverse_portfolio_optimization(
        relevant_prices,
        relevant_historical_returns,
        market_portfolio_weights,
        monthly_market_risk_premium,
        monthly_risk_free_rate)

    optimized_returns           = optimized_returns.sort_index()
    optimized_returns.index     = _replacement_values_for_tickers()
    optimized_returns           = optimized_returns.sort_index()

    return optimized_returns

def _assets():
    this_dir = os.path.dirname(__file__)
    json_dir = os.path.join(this_dir, os.pardir, 'config')
    etfs_file_path = os.path.join(json_dir, 'assets.json')

    with open(etfs_file_path) as data_file:
        assets_list = json.load(data_file)
    return assets_list

def _monthly_returns():
    return monthly_prices.pct_change()


#########
# SETUP #
#########

monthly_prices = _get_historical_prices(_get_selected_tickers()) # Default option resamples the prices as monthly means
