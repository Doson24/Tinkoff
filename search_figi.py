from tinkoff.invest import CandleInterval, Client, HistoricCandle
from datetime import timedelta, datetime
import os
from tinkoff.invest.utils import now
from pandas import DataFrame
from tinkoff.invest import Client, InstrumentStatus, SharesResponse, InstrumentIdType
from tinkoff.invest.services import InstrumentsService, MarketDataService


TOKEN = os.environ["TOKEN_test"]


CONTRACT_PREFIX = "tinkoff.public.invest.api.contract.v1."

def run(ticker):
    with Client(TOKEN) as cl:
        instruments: InstrumentsService = cl.instruments
        market_data: MarketDataService = cl.market_data

        # r = instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id="BBG004S683W7")
        # print(r)

        l = []
        for method in ['shares', 'bonds', 'etfs']:  # , 'currencies', 'futures']:
            for item in getattr(instruments, method)().instruments:
                l.append({
                    'ticker': item.ticker,
                    'figi': item.figi,
                    'type': method,
                    'name': item.name,
                })

        df = DataFrame(l)
        # df.to_json()

        df = df[df['ticker'] == ticker]
        if df.empty:
            print(f"Нет тикера {ticker}")

        # print(df.iloc[0])
        return (df['figi'].iloc[0])


def get_limits():
    with Client(TOKEN) as cl:
        tariff = cl.users.get_user_tariff()
        for unary_limit in tariff.unary_limits:
            methods = [m.replace(CONTRACT_PREFIX, "") for m in unary_limit.methods]
            print(unary_limit.limit_per_minute, "запросов в минуту для:")
            print("\t" + "\n\t".join(methods))


if __name__ == '__main__':
    tickers = ["SIBN", 'CHMF', 'ROSN', 'AFLT', 'OZON', 'YNDX', 'SBER', 'TATN', 'ALRS', 'FLOT', 'GMKN',
              'LKOH', 'TCSG', 'POLY', 'PLZL', 'VKCO']

    # tickers = ['USDRUB']
    for ticker in tickers:
        print(f'{ticker}, {run(ticker)}')