import os
from pandas import DataFrame
from datetime import timedelta, datetime
from tinkoff.invest import CandleInterval, Client, HistoricCandle
from tinkoff.invest.utils import now
from tinkoff.invest.services import InstrumentsService, MarketDataService
from backtesting import Backtest
from Ichimoku import Ichimoku_cross

# CONTRACT_PREFIX = "tinkoff.public.invest.api.contract.v1."


TOKEN = os.environ["TOKEN_test"]


def get_candles(figi: str, from_day: datetime) -> DataFrame:
    # instruments: InstrumentsService = client.instruments
    # market_data: MarketDataService = client.market_data

    # accounts = client.users.get_accounts()
    # print("\nСписок текущих аккаунтов\n")
    # for account in accounts.accounts:
    #     print("\t", account.id, account.name, account.access_level.name)
    #
    # print("\nТекущие лимиты\n")
    # tariff = client.users.get_user_tariff()
    # for unary_limit in tariff.unary_limits:
    #     methods = [m.replace(CONTRACT_PREFIX, "") for m in unary_limit.methods]
    #     print(unary_limit.limit_per_minute, "запросов в минуту для:")
    #     print("\t" + "\n\t".join(methods))
    #
    # for stream_limit in tariff.stream_limits:
    #     print(stream_limit.limit, "коннект(а/ов) для:")
    #     streams = [s.replace(CONTRACT_PREFIX, "") for s in stream_limit.streams]
    #     print("\t" + "\n\t".join(streams))
    #
    # print("\nИнформация\n")
    # info = client.users.get_info()
    # print(info)

    # При работе через market_data установлены лимиты (интервал 1H, период 365 - выдает ошибку)
    # c = client.market_data.get_candles(
    #         figi="BBG00QPYJ5H0",
    #         from_=now() - timedelta(days=365),
    #         to=now(),
    #         interval=CandleInterval.CANDLE_INTERVAL_HOUR,
    # )

    # Нет ошибок
    c = client.get_all_candles(
        figi=figi,
        from_=from_day,
        to=now(),
        interval=CandleInterval.CANDLE_INTERVAL_HOUR, )

    return create_df(c)


def get_figies(ticker: str) -> list:
    # Поиск figi по названию
    r = client.instruments.find_instrument(query=ticker)
    return [i.figi for i in r.instruments]



def create_df(candles: [HistoricCandle]) -> DataFrame:
    df = DataFrame([{
        'time': c.time,
        'Volume': c.volume,
        'Open': cast_money(c.open),
        'Close': cast_money(c.close),
        'High': cast_money(c.high),
        'Low': cast_money(c.low),
    } for c in candles])
    df.index = df.time
    print(f'[+] Get all candles ')
    return df


def get_tiker(instruments):
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


def cast_money(v):
    """
    https://tinkoff.github.io/investAPI/faq_custom_types/
    :param v:
    :return:
    """
    return v.units + v.nano / 1e9  # nano - 9 нулей


def backtesting(tiker_data):
    print(f'[+]Backtesting start')
    bt = Backtest(tiker_data, Ichimoku_cross, cash=10000, commission=.002, exclusive_orders=True)
    """
    Перебор этих значений займет 4ч:
                                 tenkan_param=range(5, 20, 1),
                                 kijun_param=range(20, 52, 1),
                                 senkou_param=range(52, 100, 1)
    """

    # stats, heatmap = bt.optimize(tenkan_param=range(5, 20, 1),
    #                              kijun_param=range(20, 52, 1),
    #                              senkou_param=range(52, 100, 1),
    #                              maximize='Equity Final [$]', return_heatmap=True
    #                              )

    stats = bt.run()
    bt.plot()
    print(stats)

    # print(stats)
    # print(stats.tail())
    # print(stats._strategy)
    # print(heatmap)
    # bt.plot(plot_volume=True, plot_pl=True)
    # heatmap.plot()


if __name__ == "__main__":

    ticker = 'TCSG'
    from_day = now() - timedelta(weeks=300)

    with Client(TOKEN) as client:
        figi = get_figies(ticker)[0]

        data = get_candles(figi, from_day)

        backtesting(data)
