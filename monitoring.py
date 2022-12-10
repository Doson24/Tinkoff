from Ichimoku import spanA, spanB, tenkan_Sen, kijun_Sen, chikou_Span
import pandas as pd
import inspect
from Ichimoku import Ichimoku_cross
import yfinance as yf
import pandas_ta as ta


class Monitor:

    def __init__(self, data: pd.DataFrame, ):
        self.position = 0
        self.data = data

    def signal_buy(self):
        if self.data.Close[-1] > self.span_A[-1] > self.span_B[-1] and \
                self.tenkan_sen[-1] > self.kijun_sen[-1] \
                and self.chikou_span[-1] > self.data.High[-26]:
            self.buy()

    def signal_sell(self):
        if self.position:
            if (self.data.Low[-1] < self.kijun_sen[-1] and self.tenkan_sen[-1] < self.kijun_sen[-1]) \
                    or self.data.Low[-1] < self.span_B[-1] \
                    or (self.data.Low[-1] < self.kijun_sen[-1] and self.tenkan_sen[-1] > self.kijun_sen[-1] and
                        self.data.Close[-2] > self.tenkan_sen[-1]):  # добавил - уменьшилась просадка
                # and (self.data.Close[-1] < self.span_A[-1] or self.data.Close[-1] < self.span_B[-1]):
                self.position.close()


def get_ichimoku(data, tenkan_param, kijun_param, senkou_param) -> pd.DataFrame:
    ichimoku = ta.ichimoku(data.High, data.Low, data.Close,
                           tenkan=tenkan_param, kijun=kijun_param, senkou=senkou_param)
    return ichimoku[0]


def main():
    tenkan_param = 9
    kijun_param = 26
    senkou_param = 52

    tiker = yf.Ticker("BABA")
    tiker_data = tiker.history(period='1y', interval='1d')
    ichimoku = get_ichimoku(tiker_data, tenkan_param, kijun_param, senkou_param)
    spanA = ichimoku.iloc(axis=1)[0]
    spanB = ichimoku.iloc(axis=1)[1]
    tenkan_Sen = ichimoku.iloc(axis=1)[2]
    kijun_Sen = ichimoku.iloc(axis=1)[3]
    chikou_Span = ichimoku.iloc(axis=1)[4]


if __name__ == '__main__':
    main()
    # code = inspect.getsource(Ichimoku_cross.next)
    # print(code)
