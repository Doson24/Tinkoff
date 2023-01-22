import datetime
import json
import os
import time

import matplotlib.pyplot as plt
from Ichimoku import spanA, spanB, tenkan_Sen, kijun_Sen, chikou_Span
import pandas as pd
import inspect
from Ichimoku import Ichimoku_cross
import yfinance as yf
import pandas_ta as ta
from main import Ticker
from tinkoff.invest.utils import now
from datetime import timedelta
from tinkoff.invest import CandleInterval, Client, HistoricCandle, RequestError, OrderDirection, OrderType


class MonitoringTiker:
    # tenkan_param = 9
    # kijun_param = 26
    # senkou_param = 52

    def __init__(self, tiker: str, figi: str, client_tinkoff,
                 from_day, position, quantity,
                 tenkan_param, kijun_param, senkou_param,
                 until_day: datetime = now(),
                 interval=CandleInterval.CANDLE_INTERVAL_HOUR
                 ):

        self.tenkan_param, self.kijun_param, self.senkou_param = int(tenkan_param), int(kijun_param), int(senkou_param)
        self.position, self.quantity = position, quantity
        self.tiker, self.figi = tiker, figi
        self.client = client_tinkoff
        self.until_day, self.from_day, self.interval = until_day, from_day, interval
        # self.data = self.download_yf()
        self.data = self.download_tinkoff()
        ichimoku = self.get_ichimoku()
        self.span_A = ichimoku.iloc(axis=1)[0]
        self.span_B = ichimoku.iloc(axis=1)[1]
        self.tenkan_sen = ichimoku.iloc(axis=1)[2]
        self.kijun_sen = ichimoku.iloc(axis=1)[3]
        self.chikou_span = ichimoku.iloc(axis=1)[4]

    def update_data(self):
        # self.data = self.download_yf()
        self.data = self.download_tinkoff()
        ichimoku = self.get_ichimoku()
        self.span_A = ichimoku.iloc(axis=1)[0]
        self.span_B = ichimoku.iloc(axis=1)[1]
        self.tenkan_sen = ichimoku.iloc(axis=1)[2]
        self.kijun_sen = ichimoku.iloc(axis=1)[3]
        self.chikou_span = ichimoku.iloc(axis=1)[4]

    def signal_buy(self):
        if not self.position:
            if self.data.Close[-1] > self.span_A[-1] > self.span_B[-1] and \
                    self.tenkan_sen[-1] > self.kijun_sen[-1] \
                    and self.chikou_span[-27] > self.data.High[-27]:
                # self.buy()
                self.position = True
                return True
        # else: return False

    def signal_sell(self):
        if self.position:
            if (self.data.Low[-1] < self.kijun_sen[-1] and self.tenkan_sen[-1] < self.kijun_sen[-1]) \
                    or self.data.Low[-1] < self.span_B[-1] \
                    or (self.data.Low[-1] < self.kijun_sen[-1] < self.tenkan_sen[-1] < self.data.Close[
                -2]):  # добавил - уменьшилась просадка
                # and (self.data.Close[-1] < self.span_A[-1] or self.data.Close[-1] < self.span_B[-1]):
                # self.position.close()
                self.position = False
                return True
        # else:return False

    def get_ichimoku(self):
        ichimoku = ta.ichimoku(self.data.High, self.data.Low, self.data.Close,
                               tenkan=self.tenkan_param, kijun=self.kijun_param, senkou=self.senkou_param)
        return ichimoku[0]

    def view(self):
        df = pd.concat([self.data.Low,
                        self.data.Close,  # self.data.iloc(axis=1)[:4],
                        self.span_A,
                        self.span_B,
                        self.tenkan_sen,
                        self.kijun_sen,
                        self.chikou_span],
                       axis=1, join='inner')
        plt.plot(df)
        plt.legend(df.columns)
        plt.show()
        # print(df)

    def tracking(self):
        now = datetime.datetime.now().strftime('%H:%M:%S')

        if self.signal_buy():
            print(f'[+] {now} {self.tiker} Buy signal')
            return 'Buy'

        elif self.signal_sell():
            print(f'[-] {now} {self.tiker} Sell signal')
            return 'Sell'
        else:
            print(f"{now} {self.tiker} Нет сигналов на сделку")
            print(f'{self.data.index.max()} - время последней свечи')
            return 'No signals'

    def buy_market(self, account_id):
        r = self.client.orders.post_order(
            order_id=str(now().timestamp()),
            figi=self.figi,
            quantity=self.quantity,
            account_id=account_id,
            direction=OrderDirection.ORDER_DIRECTION_BUY,
            order_type=OrderType.ORDER_TYPE_MARKET
        )
        return r

    def sell_market(self, account_id):
        r = self.client.orders.post_order(
            order_id=str(now().timestamp()),
            figi=self.figi,
            quantity=self.quantity,
            account_id=account_id,
            direction=OrderDirection.ORDER_DIRECTION_SELL,
            order_type=OrderType.ORDER_TYPE_MARKET
        )
        return r

    def download_yf(self, period='1d', interval='1m'):
        yf_tiker = yf.Ticker(self.tiker)
        tiker_data = yf_tiker.history(period=period, interval=interval)
        return tiker_data

    def download_tinkoff(self):

        ticker = Ticker(name=self.tiker, figi=self.figi, client_tinkoff=self.client,
                        from_day=self.from_day, until_day=self.until_day, interval=self.interval)
        return ticker.ohlc


def main():
    """
    1 Созд список с экземплярами класса
    2 Перебираем словарь с экземплярами
    3 Обновляем данные
    3 запускаем трекинг
    4 обновляем позиции в словаре
    5 задержка
    """
    # positions = {'BABA': {'position': False, 'settings': [9, 26, 52]},
    #              'TAL': {'position': True, 'settings': []},
    #              'EBS': {'position': True, 'settings': []},
    #              }
    TOKEN = os.environ["TOKEN_test_all"]
    account_id = os.environ['account_id']

    with open('settings_track.json', 'r', encoding='utf8') as f:
        moex_positions = json.load(f)

    settings_tickers = moex_positions
    delay = 60 * 1
    from_day = now() - timedelta(days=31)

    list_obj = []
    with Client(TOKEN) as client:
        for tiker, param in settings_tickers.items():
            mon_tiker = MonitoringTiker(tiker=tiker,
                                        figi=param['figi'],
                                        client_tinkoff=client,
                                        from_day=from_day,
                                        position=param['position'],
                                        quantity=param['quantity'],
                                        tenkan_param=param['settings'][0],
                                        kijun_param=param['settings'][1],
                                        senkou_param=param['settings'][2])
            list_obj.append(mon_tiker)

        time.sleep(delay)
        print(f'Data uploaded \nSleep {delay}s')

        try:
            while True:
                for count, obj in enumerate(list_obj[:]):
                    obj.update_data()
                    signal = obj.tracking()

                    if signal == "Buy":
                        obj.buy_market(account_id)
                    elif signal == "Sell":
                        obj.sell_market(account_id)

                    # obj.view()
                    # обновление позиции в словаре обьектов для вывода
                    settings_tickers[obj.tiker]['position'] = obj.position
                print('_' * 45)
                time.sleep(delay)
        except KeyboardInterrupt:
            with open('savepoint.json', "w", encoding='utf8') as f:
                json.dump(settings_tickers, f, indent=6)
            print(settings_tickers)
            # list_obj[2].view()


if __name__ == '__main__':
    main()
    # code = inspect.getsource(Ichimoku_cross.next)
    # print(code)
