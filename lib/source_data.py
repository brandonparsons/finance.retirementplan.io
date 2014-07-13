import datetime
import pandas as pd
import pandas.io.data as web
import Quandl

start       = datetime.datetime(2000, 1, 1).date()
end         = datetime.date.today()
data_source = 'yahoo' # 'google'

def getTickerData(ticker):
    """
    :param ticker: string, Yahoo finance ticker
    :return: pandas DataFrame of ticker Close data
    """
    return web.DataReader(ticker, data_source, start, end)

def get_prices(tickers, use_adjusted=True):
    """
    :param tickers: list of tickers as strings
    :param use_adjusted: boolean, whether to use the adjusted close if available or not
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

    # Resample to monthly. We only have monthly data for real estate, and we
    # are doing monthly simulations anyway as weekly gets to resource-intensive
    df = df.resample('M', how='mean')

    return df

def get_real_estate():
    """
    :param (none)
    :return: pandas DataFrame of real estate data (Case-Schiller)
    """

    # Trimming to 2007-10-01 to be on ~ the same timescale as have data for all
    # other securities.
    df = Quandl.get("SANDP/HPI_COMPOSITE10_SA", trim_start="2007-10-01")
    return df['Index']

def get_inflation():
    """
    :param (none)
    :return: pandas DataFrame of inflation data (Bank of Canada)
    """

    # Trimming to 2007-10-01 to be on ~ the same timescale as have data for all
    # other securities.
    df = Quandl.get("BOC/CDA_CPI", trim_start="2007-10-01")
    return df['Core CPI']
