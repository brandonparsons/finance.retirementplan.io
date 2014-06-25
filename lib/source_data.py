import datetime
import pandas as pd
import pandas.io.data as web

start       = datetime.datetime(2000, 1, 1).date()
end         = datetime.date.today()
data_source = 'yahoo' # 'google'

def getTickerData(ticker):
    """
    :param ticker: string, Yahoo finance ticker
    :return: pandas DataFrame of ticker Close data
    """
    return web.DataReader(ticker, data_source, start, end)

def get_prices(tickers, use_adjusted=True, resample=False):
    """
    :param tickers: list of tickers as strings
    :param use_adjusted: boolean, whether to use the adjusted close if available or not
    :param resample: false if no resampling. Otherwise 'W', 'M' (weekly/monthly)
    :return: pandas DataFrame of asset prices
    """

    df = pd.DataFrame()

    for ticker in tickers:
        # authtoken = os.getenv('QUANDL_TOKEN', '')
        # data = Quandl.get(ticker, authtoken=authtoken, transformation=transformation)
        data = getTickerData(ticker)
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

    # If you want to work with weekly or monthly prices:
    if resample:
        df = df.resample(resample) # 'W' for weekly, 'M' for monthly

    return df
