import math
import os

import pandas as pd
import pytz
from pandas import DataFrame
from datetime import timedelta, datetime
from tinkoff.invest import CandleInterval, Client, HistoricCandle
from tinkoff.invest.utils import now
from tinkoff.invest.services import InstrumentsService, MarketDataService
from backtesting import Backtest
from yfinance import ticker

from Ichimoku import Ichimoku_cross
import yfinance
from backtesting import _plotting


def get_candles(figi: str, from_day: datetime, interval=CandleInterval.CANDLE_INTERVAL_DAY) -> DataFrame:
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
        interval=interval, )

    return create_df(c)


def get_figies(ticker: str) -> list:
    # Поиск figi по названию
    r = client.instruments.find_instrument(query=ticker)
    # return [i.figi for i in r.instruments]
    return r.instruments


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
    for method in ['shares', 'bonds', 'etfs', 'currencies', 'futures']:
        for item in getattr(instruments, method)().instruments:
            l.append({
                'ticker': item.ticker,
                'figi': item.figi,
                'type': method,
                'name': item.name,
            })

    df = DataFrame(l)
    return df


def cast_money(v):
    """
    https://tinkoff.github.io/investAPI/faq_custom_types/
    :param v:
    :return:
    """
    return v.units + v.nano / 1e9  # nano - 9 нулей


def view_save_plot(ticker, stats, bt):
    try:
        bt.plot(plot_volume=True, plot_pl=True, filename=f'data/{ticker}_'
                                                         f'{stats._strategy.tenkan_param}-{stats._strategy.kijun_param}-'
                                                         f'{stats._strategy.senkou_param}')
    except Exception as ex:
        print('ERORR', '-' * 180)


def backtesting(ticker, tiker_data):
    print(f'[+]Backtesting start')
    bt = Backtest(tiker_data, Ichimoku_cross, cash=10000, commission=.002, exclusive_orders=True)

    stats = bt.run()
    view_save_plot(ticker, stats, bt)
    # print(stats)
    return stats


def backtesting_optimize(ticker, tiker_data, maximize):
    print(f'[+]Backtesting optimize start')
    bt = Backtest(tiker_data, Ichimoku_cross, cash=10000, commission=.002, exclusive_orders=True)
    """
    Перебор этих значений займет 4ч:
                                 tenkan_param=range(5, 20, 1),
                                 kijun_param=range(20, 52, 1),
                                 senkou_param=range(52, 100, 1)
    """
    # stats, heatmap = bt.optimize(tenkan_param=range(8, 10, 1),
    #                              kijun_param=range(15, 17, 1),
    #                              senkou_param=range(60, 70, 1),
    #                              maximize=maximize, return_heatmap=True
    #                              )

    stats, heatmap = bt.optimize(tenkan_param=range(4, 15, 1),
                                 kijun_param=range(15, 35, 1),
                                 senkou_param=range(45, 80, 1),
                                 maximize=maximize, return_heatmap=True
                                 )

    # stats = bt.run()
    # bt.plot()
    # print(stats)

    # print(ticker)
    # print(stats)
    # print(stats.tail())
    # print(stats._strategy)
    # print(heatmap)
    view_save_plot(ticker, stats, bt)
    # heatmap.plot()
    return stats


def transform_stats(ticker: str, maximize: str, stats, interval: str) -> str:
    """
    :param ticker:
    :param maximize:
    :param stats:
    :return:
    """
    stats_dict = stats.to_dict()
    column_stats = list(stats_dict.keys())[:27]  # статистика до SQN
    filter_stats_dict = {key: stats_dict.get(key) for key in column_stats}
    # stats_df = pd.DataFrame([filter_stats_dict])
    stats_str = [str(i) for i in list(filter_stats_dict.values())]

    tenkan_optimaze = stats._strategy.tenkan_param
    kijun_optimaze = stats._strategy.kijun_param
    senkou_optimaze = stats._strategy.senkou_param

    stats_str.insert(0, str(senkou_optimaze))
    stats_str.insert(0, str(kijun_optimaze))
    stats_str.insert(0, str(tenkan_optimaze))
    stats_str.append(maximize)
    stats_str.append(interval)
    stats_str.insert(0, ticker)
    return ', '.join(stats_str) + '\n'


def save_file(line):
    with open('stats.csv', 'a') as f:
        f.write(line)


def open_file_figies():
    df_figies = pd.read_csv('tiker_for_search.csv')
    return df_figies


def train_param(candels):
    # """Тест на 70% данных"""
    size_train = 0.80
    size_end = 0.90

    # train_candels = candels[:math.floor(len(candels) * size_train)]
    train_end = candels[:math.floor(len(candels) * size_end)]

    # stats = backtesting_optimize(tickers[i], train_candels, maximize=maximize_optimizer)
    # stats_full = backtesting_optimize(tickers[i], train_end, maximize=maximize_optimizer)

    stats = backtesting(tickers[i], train_end)
    # tenkan = stats._strategy.tenkan_param
    # kijun = stats._strategy.kijun_param
    # senkou = stats._strategy.senkou_param

    # tenkan_optimaze = stats_full._strategy.tenkan_param
    # kijun_optimaze = stats_full._strategy.kijun_param
    # senkou_optimaze = stats_full._strategy.senkou_param
    #
    print(f'{tenkan} - {kijun} - {senkou}')
    print(f'{tenkan_optimaze} - {kijun_optimaze} - {senkou_optimaze}')
    """END"""


if __name__ == "__main__":
    # CONTRACT_PREFIX = "tinkoff.public.invest.api.contract.v1."
    TOKEN = os.environ["TOKEN_test"]

    # ['ES=F', "KWEB"]
    tickers = ['SBER']
    figies = ['BBG004730N88']
    # tickers = open_file_figies().Name
    # figies = open_file_figies().figi
    interval = CandleInterval.CANDLE_INTERVAL_DAY

    maximize_optimizer = 'Return [%]'
    from_day = now() - timedelta(weeks=52 * 12)
    # from_day = datetime(2006, 1, 1)
    # end_day = datetime(2015, 4, 30)
    # _plotting._MAX_CANDLES = 20_000             #тест избавления от ошибки

    with Client(TOKEN) as client:
        # for i in get_figies(ticker):
        #     print(i.name)
        # figi = get_figies(ticker)[0].figi
        # print(figi)

        for i in range(len(tickers)):
            candels = get_candles(figies[i], from_day, interval)

            # data_yfin = yfinance.download(ticker, start=from_day, interval='1d')

            # Без оптимизатора
            # stats = backtesting(tickers[i], candels)
            # line = transform_stats(ticker=tickers[i], stats=stats, maximize=maximize_optimizer, interval=interval._name_)
            # save_file(line)

            # С оптимизатором
            # stats = backtesting_optimize(tickers[i], candels, maximize=maximize_optimizer)
            # line = transform_stats(ticker=tickers[i], stats=stats, maximize=maximize_optimizer, interval=interval._name_)
            # save_file(line)

            train_param(candels)
