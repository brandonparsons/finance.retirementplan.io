import datetime
import pandas as pd
import pandas.io.data as web
import Quandl
import ystockquote

start = datetime.datetime(2000, 1, 1).date()
end = datetime.date.today()
data_source = 'yahoo' # 'google'

def getTickerData(ticker):
    """
    :param ticker: string, Yahoo finance ticker
    :return: pandas DataFrame of ticker Close data
    """
    return web.DataReader(ticker, data_source, start, end)

def get_historical_prices(tickers, use_adjusted=True, resample_monthly=True):
    """
    Obtains resampled historical adjusted close prices for tickers.
    :param tickers: list of tickers as strings
    :param use_adjusted: boolean, whether to use the adjusted close if available or not
    :param resample_monthly: boolean, whether to resample to monthly values or not
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

    # Resample to monthly:
    # - We only have monthly data for real estate index (for simulation - not ETFs)
    # - Monthly mean/variance is statistically more relevant for long-term investors (smooths short-term volatility)
    # - T-Bill returns used in reverse portfolio optimization only have monthly/annual values - timeframes need to line up
    # - Doing monthly monte carlo simulations weekly gets to resource-intensive
    if resample_monthly:
        df = df.resample('M', how='mean')

    return df

def get_last_prices(tickers):
    """
    Obtains last quotes for tickers.
    :param tickers: list of tickers as strings
    :return: dict of quotes e.g. {'NAESX': 54.94, 'VDMIX': 11.5, 'XSB.TO': 28.63}
    """
    return { ticker: float(ystockquote.get_price(ticker)) for ticker in tickers }

def get_real_estate():
    """
    Obtains monthly historical prices for real estate via Case-Schiller index.
    :param (none)
    :return: pandas DataFrame of real estate data
    """
    # Trimming to 2007-10-01 to be on ~ the same timescale as have data for all
    # other securities.
    #
    df = Quandl.get("SANDP/HPI_COMPOSITE10_SA", trim_start="2007-10-01", collapse="monthly")
    return df['Index']

def get_inflation():
    """
    Obtains monthly historical inflation data for Canada via Bank of Canada
    :param (none)
    :return: pandas DataFrame of inflation data
    """
    # Trimming to 2007-10-01 to be on ~ the same timescale as have data for all
    # other securities.
    df = Quandl.get("BOC/CDA_CPI", trim_start="2007-10-01")

    return df['Core CPI']

def get_tbill():
    """
    Obtains monthly historical TBill returns from the U.S. Treasury, which will
    be assumed to be a good proxy for the "Risk Free Rate"
    :param (none)
    :return: pandas DataFrame of TBill data
    """
    df = Quandl.get("WREN/W10", trim_start="2000-01-31", collapse="monthly")
    return df['Value']
