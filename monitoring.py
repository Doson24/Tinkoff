import matplotlib.pyplot as plt
from Ichimoku import spanA, spanB, tenkan_Sen, kijun_Sen, chikou_Span
import pandas as pd
import inspect
from Ichimoku import Ichimoku_cross
import yfinance as yf
import pandas_ta as ta


class Monitor:
    tenkan_param = 9
    kijun_param = 26
    senkou_param = 52

    def __init__(self, data: pd.DataFrame):
        self.data = data
        ichimoku = self.get_ichimoku()
        self.span_A = ichimoku.iloc(axis=1)[0]
        self.span_B = ichimoku.iloc(axis=1)[1]
        self.tenkan_sen = ichimoku.iloc(axis=1)[2]
        self.kijun_sen = ichimoku.iloc(axis=1)[3]
        self.chikou_span = ichimoku.iloc(axis=1)[4]

    def signal_buy(self):
        if self.data.Close[-1] > self.span_A[-1] > self.span_B[-1] and \
                self.tenkan_sen[-1] > self.kijun_sen[-1] \
                and self.chikou_span[-27] > self.data.High[-27]:
            # self.buy()
            print('BUY!!!')

    def signal_sell(self):
        if (self.data.Low[-1] < self.kijun_sen[-1] and self.tenkan_sen[-1] < self.kijun_sen[-1]) \
                or self.data.Low[-1] < self.span_B[-1] \
                or (self.data.Low[-1] < self.kijun_sen[-1] < self.tenkan_sen[-1] < self.data.Close[-2]):  # добавил - уменьшилась просадка
            # and (self.data.Close[-1] < self.span_A[-1] or self.data.Close[-1] < self.span_B[-1]):
            # self.position.close()
            print("SELL!!!")

    def get_ichimoku(self):
        ichimoku = ta.ichimoku(self.data.High, self.data.Low, self.data.Close,
                               tenkan=self.tenkan_param, kijun=self.kijun_param, senkou=self.senkou_param)
        return ichimoku[0]

    def view(self):
        df = pd.concat([self.data.Close, #self.data.iloc(axis=1)[:4],
                        self.span_A,
                        self.span_B,
                        self.tenkan_sen,
                        self.kijun_sen,
                        self.chikou_span],
                       axis=1, join='inner')
        plt.plot(df)
        plt.show()


def main():
    tiker = yf.Ticker("BABA")
    tiker_data = tiker.history(period='1y', interval='1d')
    ticker1 = Monitor(tiker_data)
    ticker1.signal_buy()
    # ticker1.view()


if __name__ == '__main__':
    main()
    # code = inspect.getsource(Ichimoku_cross.next)
    # print(code)
