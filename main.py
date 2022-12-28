import math
import os
import time

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


def get_figies(ticker: str) -> list:
    # Поиск figi по названию
    r = client.instruments.find_instrument(query=ticker)
    # return [i.figi for i in r.instruments]
    return r.instruments


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


def transform_stats(ticker: str, maximize: str, stats, interval: str) -> str:
    """
    Преобразование статистики в строку через запятую для дальнейшего сохранения в csv файл

    :param ticker: имя
    :param maximize: что максимизируем
    :param stats: остальная статистика
    :return: строка со статистикой через запятую
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


def open_file():
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

    # stats = backtesting(tickers[i], train_end)
    # tenkan = stats._strategy.tenkan_param
    # kijun = stats._strategy.kijun_param
    # senkou = stats._strategy.senkou_param

    # tenkan_optimaze = stats_full._strategy.tenkan_param
    # kijun_optimaze = stats_full._strategy.kijun_param
    # senkou_optimaze = stats_full._strategy.senkou_param
    #
    # print(f'{tenkan} - {kijun} - {senkou}')
    # print(f'{tenkan_optimaze} - {kijun_optimaze} - {senkou_optimaze}')
    """END"""


class Ticker:
    maximize_optimizer = 'Return [%]'

    def __init__(self, name: str, figi: str,
                 client_tinkoff,
                 from_day: datetime, until_day: datetime = now(),
                 interval=CandleInterval.CANDLE_INTERVAL_HOUR
                 ):
        self.name = name
        self.figi = figi
        self.interval = interval
        self.from_day = from_day
        self.until_day = until_day
        self.client = client_tinkoff
        self.candels = self.download_candles(self.client, self.figi, self.from_day, self.until_day, self.interval)
        self.ohlc = self.create_df(self.candels)
        self.stats = None

    @staticmethod
    def download_candles(client, figi: str, from_day: datetime, until_day: datetime, interval: CandleInterval) -> [
        HistoricCandle]:
        """
        Загрузка свечей от Тинькофф

        :param client:
        :param figi:
        :param from_day: от какого дня
        :param until_day: до какого дня
        :param interval: интервал (1мин, 5мин, 15мин, 1час, 1 день)

        :return: свечи в сыром виде
        """
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
        candels = client.get_all_candles(
            figi=figi,
            from_=from_day,
            to=until_day,
            interval=interval, )

        return candels

    def create_df(self, candles: [HistoricCandle]) -> DataFrame:
        """
        Преобразование свечей в датафрейм

        :param candles: свечи в сыром виде от Тинькоф
        :return: Готовый датафрейм
        """
        df = DataFrame([{
            'time': c.time,
            'Volume': c.volume,
            'Open': self.cast_money(c.open),
            'Close': self.cast_money(c.close),
            'High': self.cast_money(c.high),
            'Low': self.cast_money(c.low),
        } for c in candles])
        df.index = df.time
        print(f'[+] Get all candles ')
        return df

    # def view_save_plot(self, bt):
    #     try:
    #         bt.plot(plot_volume=True, plot_pl=True, filename=
    #                                          f'data/{self.name}_'
    #                                          f'{self.stats._strategy.tenkan_param}-{self.stats._strategy.kijun_param}-'
    #                                          f'{self.stats._strategy.senkou_param}')
    #     except Exception as ex:
    #         print('ERORR', '-' * 180)

    def dowload_ohlc_3years(self):
        """
        Загрузка свечей за период в 3 года

        :return: Готовый скеенный датафрейм
        """
        from_day = [now() - timedelta(weeks=52), now() - timedelta(weeks=52 * 2), now() - timedelta(weeks=52 * 3)]
        until_day = [now(), from_day[0], from_day[1]]
        sum_candels = pd.DataFrame()
        for num in range(len(from_day)):
            try:
                candels = self.download_candles(client=self.client, figi=self.figi,
                                                from_day=from_day[num], until_day=until_day[num],
                                                interval=self.interval, )
                candels = self.create_df(candels)
                sum_candels = pd.concat([sum_candels, candels])
                time.sleep(3)
            except AttributeError:
                print('[-] Нет данных')
        return sum_candels

    @staticmethod
    def cast_money(v):
        """
        https://tinkoff.github.io/investAPI/faq_custom_types/
        :param v: value
        :return:
        """
        return v.units + v.nano / 1e9  # nano - 9 нулей

    @staticmethod
    def save_file(line):
        """
        Добавление статистики в файл stats.csv

        :param line: строка статистики
        :return:
        """
        with open('stats.csv', 'a') as f:
            f.write(line)


def view_save_plot(ticker, stats, bt):
    """
    Отображение и сохранение графика в папку data/

    :param ticker:
    :param stats:
    :param bt:
    :return:
    """
    try:
        bt.plot(plot_volume=True, plot_pl=True, filename=f'data/{ticker}_'
                                                         f'{stats._strategy.tenkan_param}-{stats._strategy.kijun_param}-'
                                                         f'{stats._strategy.senkou_param}')
    except Exception as ex:
        print('ERORR', '-' * 180)


def backtesting(ticker, tiker_data):
    """
    Функция Бэктестинга с сохранением и отображением графика

    :param ticker: название
    :param tiker_data: OHLC
    :return: статистика
    """
    print(f'[+]Backtesting start')
    bt = Backtest(tiker_data, Ichimoku_cross, cash=10000, commission=.002, exclusive_orders=True)

    stats = bt.run()
    view_save_plot(ticker, stats, bt)
    # print(stats)
    return stats


def backtesting_optimize(ticker: str, tiker_data: pd.DataFrame, maximize: str):
    """
    Бэктестинг с оптимизацией параметров

    :param ticker: имя
    :param tiker_data: OHLC
    :param maximize: что максимизируем
    :return: статистика
    """

    print(f'[+]Backtesting optimize start {now() + timedelta(hours=7)}')
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


if __name__ == "__main__":
    # CONTRACT_PREFIX = "tinkoff.public.invest.api.contract.v1."
    TOKEN = os.environ["TOKEN_test"]
    # ['ES=F', "KWEB"]
    # tickers = ['BABA']
    # figies = ['BBG006G2JVL2']

    tickers = open_file().Name
    figies = open_file().figi

    interval = CandleInterval.CANDLE_INTERVAL_DAY
    maximize_optimizer = 'Return [%]'
    from_day = now() - timedelta(weeks=52)
    # from_day = datetime(2006, 1, 1)
    # end_day = datetime(2015, 4, 30)
    # _plotting._MAX_CANDLES = 20_000             #тест избавления от ошибки

    with Client(TOKEN) as client:

        for i in range(len(tickers)):
            # Список интервалов по 1 году
            # candels = concat_candels()
            # candels = get_candles(figies[i], from_day=from_day, interval=interval)
            # data_yfin = yfinance.download(ticker, start=from_day, interval='1d')

            # train_param(candels)

            """Тест работы с помощью класса"""
            ticker = Ticker(name=tickers[i], figi=figies[i], client_tinkoff=client, from_day=from_day,
                            # interval=interval
                            )
            candels = ticker.dowload_ohlc_3years()
            # candels = ticker.ohlc

            # Без оптимизатора
            # stats = backtesting(tickers[i], candels)

            # С оптимизатором
            stats = backtesting_optimize(tickers[i], candels, maximize=maximize_optimizer)

            line = transform_stats(ticker=tickers[i], stats=stats, maximize=maximize_optimizer,
                                   interval=interval._name_)
            Ticker.save_file(line)
