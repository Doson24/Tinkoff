import datetime

from backtesting.test import GOOG
from backtesting.lib import crossover
from backtesting import Strategy
from tinkoff.invest.utils import now
import pandas_ta as ta
from backtesting import Backtest
import yfinance as yf
import pandas as pd
from datetime import timedelta


def spanA(data, tenkan_param, kijun_param, senkou_param):
    # Data OHLCV
    #что такое s?
    ichimoku = ta.ichimoku(data.High.s, data.Low.s, data.Close.s,
                           tenkan=tenkan_param, kijun=kijun_param, senkou=senkou_param)
    # print(ichimoku[0].to_numpy().T)
    return ichimoku[0].to_numpy().T[0]


def spanB(data, tenkan_param, kijun_param, senkou_param):
    # Data OHLCV
    ichimoku = ta.ichimoku(data.High.s, data.Low.s, data.Close.s,
                           tenkan=tenkan_param, kijun=kijun_param, senkou=senkou_param)
    return ichimoku[0].to_numpy().T[1]


def tenkan_Sen(data, tenkan_param, kijun_param, senkou_param):
    # Data OHLCV
    ichimoku = ta.ichimoku(data.High.s, data.Low.s, data.Close.s,
                           tenkan=tenkan_param, kijun=kijun_param, senkou=senkou_param)
    return ichimoku[0].to_numpy().T[2]


def kijun_Sen(data, tenkan_param, kijun_param, senkou_param):
    # Data OHLCV
    ichimoku = ta.ichimoku(data.High.s, data.Low.s, data.Close.s,
                           tenkan=tenkan_param, kijun=kijun_param, senkou=senkou_param)
    return ichimoku[0].to_numpy().T[3]


def chikou_Span(data, tenkan_param, kijun_param, senkou_param):
    # Data OHLCV
    ichimoku = ta.ichimoku(data.High.s, data.Low.s, data.Close.s,
                           tenkan=tenkan_param, kijun=kijun_param, senkou=senkou_param)
    return ichimoku[0].to_numpy().T[4]


class Ichimoku_cross(Strategy):
    tenkan_param = 9
    kijun_param = 26
    senkou_param = 52

    def init(self):
        """Ichimoku attributes"""
        self.span_A = self.I(spanA, self.data, self.tenkan_param, self.kijun_param, self.senkou_param)
        self.span_B = self.I(spanB, self.data, self.tenkan_param, self.kijun_param, self.senkou_param)
        self.tenkan_sen = self.I(tenkan_Sen, self.data, self.tenkan_param, self.kijun_param, self.senkou_param)
        self.kijun_sen = self.I(kijun_Sen, self.data, self.tenkan_param, self.kijun_param, self.senkou_param)
        self.chikou_span = self.I(chikou_Span, self.data, self.tenkan_param, self.kijun_param, self.senkou_param)
        """Other atrributes"""

    def next(self):
        """
        Вход :
            Если цена выше зеленного облака,
            ten выше kij,
            Отстающая выше High цены в прошлом
        Выход :
            Если цена Low ниже kij,                     СРАВНИТЬ CLOSE И LOW
            ten < kij
        """
        """
         if self.position:
            if self.data.Close[-1] < self.kijun_sen[-1] \
                    and self.tenkan_sen[-1] < self.kijun_sen[-1]: \
                    # and (self.data.Close[-1] < self.span_A[-1] or self.data.Close[-1] < self.span_B[-1]):
                self.position.close()

         else:
            if self.data.Close[-1] > self.span_A[-1] > self.span_B[-1] and \
                    self.tenkan_sen[-1] > self.kijun_sen[-1] and \
                    self.chikou_span[-1] > self.data.Close[-26]:
                self.buy()
        """

        if self.position:
            if (self.data.Low[-1] < self.kijun_sen[-1] and self.tenkan_sen[-1] < self.kijun_sen[-1])\
                    or self.data.Low[-1] < self.span_B[-1] \
                    or (self.data.Low[-1] < self.kijun_sen[-1] < self.tenkan_sen[-1] < self.data.Close[-2]):  #добавил - уменьшилась просадка
                    # and (self.data.Close[-1] < self.span_A[-1] or self.data.Close[-1] < self.span_B[-1]):
                self.position.close()

        else:
            if self.data.Close[-1] > self.span_A[-1] > self.span_B[-1] and \
                    self.tenkan_sen[-1] > self.kijun_sen[-1] \
                    and self.chikou_span[-1] > self.data.High[-26]:
                self.buy()
                # self.buy(sl=self.span_B[-1])


if __name__ == '__main__':
    tiker = yf.Ticker("BABA")
    """
    Для интервала в "1h" данные только за последние 730 дней
    """
    from_day = now() - timedelta(weeks=600)

    tiker_data = tiker.history(period='max', interval='1d')

    bt = Backtest(tiker_data, Ichimoku_cross, cash=10000, commission=.002, exclusive_orders=True)
    """
    Перебор этих значений займет 4ч:
                                 tenkan_param=range(5, 20, 1),
                                 kijun_param=range(20, 52, 1),
                                 senkou_param=range(52, 100, 1)
    """
    stats = bt.run()
    bt.plot()
    print(stats)
    maximize = 'Return [%]'
    # stats, heatmap = bt.optimize(tenkan_param=range(8, 10, 1),
    #                              kijun_param=range(15, 17, 1),
    #                              senkou_param=range(60, 70, 1),
    #                              maximize=maximize, return_heatmap=True
    #                              )


    # print(stats)
    # print(stats.tail())
    # print(stats._strategy)
    # print(heatmap)
    # bt.plot(plot_volume=True, plot_pl=True)
    # heatmap.plot()
