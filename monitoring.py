import datetime
import json
import time

import matplotlib.pyplot as plt
from Ichimoku import spanA, spanB, tenkan_Sen, kijun_Sen, chikou_Span
import pandas as pd
import inspect
from Ichimoku import Ichimoku_cross
import yfinance as yf
import pandas_ta as ta


class MonitoringTiker:
    # tenkan_param = 9
    # kijun_param = 26
    # senkou_param = 52

    def __init__(self, tiker, position, tenkan_param, kijun_param, senkou_param):
        self.tenkan_param = int(tenkan_param)
        self.kijun_param = int(kijun_param)
        self.senkou_param = int(senkou_param)
        self.position = position
        self.tiker = tiker
        self.data = self.download_yf()
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
                    or (self.data.Low[-1] < self.kijun_sen[-1] < self.tenkan_sen[-1] < self.data.Close[-2]):  # добавил - уменьшилась просадка
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

        elif self.signal_sell():
            print(f'[-] {now} {self.tiker} Sell signal')

        else:
            print(f"{now} {self.tiker} Нет сигналов на сделку")
            print(f'{self.data.index.max()}')

    def download_yf(self, period='1d', interval='1m'):
        yf_tiker = yf.Ticker(self.tiker)
        tiker_data = yf_tiker.history(period=period, interval=interval)
        return tiker_data


def main():
    """
    1 Созд список с экземплярами класса
    2 Перебираем словарь с экземплярами
    3 запускаем трекинг
    4 обновляем позиции в словаре
    5 задержка
    """
    # positions = {'BABA': {'position': False, 'settings': [9, 26, 52]},
    #              'TAL': {'position': True, 'settings': []},
    #              'EBS': {'position': True, 'settings': []},
    #              }

    with open('settings_track.json', 'r', encoding='utf8') as f:
        moex_positions = json.load(f)

    positions = moex_positions
    delay = 10

    list_obj = []
    for tiker, param in positions.items():
        mon_tiker = MonitoringTiker(tiker,
                                    position=param['position'],
                                    tenkan_param=param['settings'][0],
                                    kijun_param=param['settings'][1],
                                    senkou_param=param['settings'][2])
        list_obj.append(mon_tiker)

    try:
        while True:
            for obj in list_obj[0:1]:
                obj.data = obj.download_yf()
                obj.tracking()
                obj.view()
                positions[obj.tiker] = obj.position
            print('_'*45)
            time.sleep(delay)
    except KeyboardInterrupt:
        print(positions)
        # list_obj[2].view()


if __name__ == '__main__':
    main()
    # code = inspect.getsource(Ichimoku_cross.next)
    # print(code)
