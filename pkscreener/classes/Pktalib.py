"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import warnings
from time import sleep

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd

from pkscreener import Imports
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger

if Imports["talib"]:
    import talib
else:
    try:
        import pandas_ta as talib

        print(
            colorText.BOLD
            + colorText.FAIL
            + "[+] TA-Lib is not installed. Falling back on pandas_ta.\n[+] For full coverage(candle patterns), you may wish to follow instructions from\n[+] https://github.com/ta-lib/ta-lib-python"
            + colorText.END
        )
        sleep(3)
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        import talib


class pktalib:
    @classmethod
    def EMA(self, close, timeperiod):
        try:
            return talib.ema(close, timeperiod)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.EMA(close, timeperiod)

    @classmethod
    def SMA(self, close, timeperiod):
        try:
            return talib.sma(close, timeperiod)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.SMA(close, timeperiod)

    @classmethod
    def MA(self, close, timeperiod):
        try:
            return talib.ma(close, timeperiod)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.MA(close, timeperiod)

    @classmethod
    def MACD(self, close, fast, slow, signal):
        try:
            return talib.macd(close, fast, slow, signal,talib=Imports["talib"])
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.MACD(close, fast, slow, signal)

    @classmethod
    def RSI(self, close, timeperiod):
        try:
            return talib.rsi(close, timeperiod)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.RSI(close, timeperiod)

    @classmethod
    def CCI(self, high, low, close, timeperiod):
        try:
            return talib.cci(high, low, close, timeperiod)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CCI(high, low, close, timeperiod)

    @classmethod
    def Aroon(self, high, low, timeperiod):
        try:
            return talib.aroon(high, low, timeperiod)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            aroon_down, aroon_up = talib.AROON(high, low, timeperiod)
            aroon_up.name = f"AROONU_{timeperiod}"
            aroon_down.name = f"AROOND_{timeperiod}"
            data = {
                aroon_down.name: aroon_down,
                aroon_up.name: aroon_up,
            }
            return pd.DataFrame(data)
        
    @classmethod
    def STOCHRSI(self, close, timeperiod, fastk_period, fastd_period, fastd_matype):
        try:
            _name = "STOCHRSI"
            _props = f"_{timeperiod}_{timeperiod}_{fastk_period}_{fastd_period}"
            stochrsi_kname = f"{_name}k{_props}"
            stochrsi_dname = f"{_name}d{_props}"
            df = talib.stochrsi(
                close,
                length=timeperiod,
                rsi_length=timeperiod,
                k=fastk_period,
                d=fastd_period,
                mamode=fastd_matype,
            )
            return df[stochrsi_kname], df[stochrsi_dname]
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.STOCHRSI(
                close.values, timeperiod, fastk_period, fastd_period, fastd_matype
            )

    @classmethod
    def ichimoku(
        self, df, tenkan=None, kijun=None, senkou=None, include_chikou=True, offset=None
    ):
        import pandas_ta as ta

        ichimokudf, spandf = ta.ichimoku(
            df["high"], df["low"], df["close"], tenkan, kijun, senkou, False, 26
        )
        return ichimokudf

    @classmethod
    def CDLMORNINGSTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "morningstar")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLMORNINGSTAR(open, high, low, close)

    @classmethod
    def CDLMORNINGDOJISTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "morningdojistar")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLMORNINGDOJISTAR(open, high, low, close)

    @classmethod
    def CDLEVENINGSTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "eveningstar")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLEVENINGSTAR(open, high, low, close)

    @classmethod
    def CDLEVENINGDOJISTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "eveningdojistar")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLEVENINGDOJISTAR(open, high, low, close)

    @classmethod
    def CDLLADDERBOTTOM(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "ladderbottom")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLLADDERBOTTOM(open, high, low, close)

    @classmethod
    def CDL3LINESTRIKE(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3linestrike")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDL3LINESTRIKE(open, high, low, close)

    @classmethod
    def CDL3BLACKCROWS(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3blackcrows")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDL3BLACKCROWS(open, high, low, close)

    @classmethod
    def CDL3INSIDE(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3inside")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDL3INSIDE(open, high, low, close)

    @classmethod
    def CDL3OUTSIDE(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3outside")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDL3OUTSIDE(open, high, low, close)

    @classmethod
    def CDL3WHITESOLDIERS(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3whitesoldiers")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDL3WHITESOLDIERS(open, high, low, close)

    @classmethod
    def CDLHARAMI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "harami")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLHARAMI(open, high, low, close)

    @classmethod
    def CDLHARAMICROSS(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "haramicross")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLHARAMICROSS(open, high, low, close)

    @classmethod
    def CDLMARUBOZU(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "marubozu")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLMARUBOZU(open, high, low, close)

    @classmethod
    def CDLHANGINGMAN(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "hangingman")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLHANGINGMAN(open, high, low, close)

    @classmethod
    def CDLHAMMER(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "hammer")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLHAMMER(open, high, low, close)

    @classmethod
    def CDLINVERTEDHAMMER(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "invertedhammer")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLINVERTEDHAMMER(open, high, low, close)

    @classmethod
    def CDLSHOOTINGSTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "shootingstar")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLSHOOTINGSTAR(open, high, low, close)

    @classmethod
    def CDLDRAGONFLYDOJI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "dragonflydoji")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLDRAGONFLYDOJI(open, high, low, close)

    @classmethod
    def CDLGRAVESTONEDOJI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "gravestonedoji")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLGRAVESTONEDOJI(open, high, low, close)

    @classmethod
    def CDLDOJI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "doji")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLDOJI(open, high, low, close)

    @classmethod
    def CDLENGULFING(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "engulfing")
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return talib.CDLENGULFING(open, high, low, close)

    @classmethod
    def argrelextrema(self, data, comparator, axis=0, order=1, mode="clip"):
        """
        Calculate the relative extrema of `data`.

        Relative extrema are calculated by finding locations where
        ``comparator(data[n], data[n+1:n+order+1])`` is True.

        Parameters
        ----------
        data : ndarray
            Array in which to find the relative extrema.
        comparator : callable
            Function to use to compare two data points.
            Should take two arrays as arguments.
        axis : int, optional
            Axis over which to select from `data`. Default is 0.
        order : int, optional
            How many points on each side to use for the comparison
            to consider ``comparator(n,n+x)`` to be True.
        mode : str, optional
            How the edges of the vector are treated. 'wrap' (wrap around) or
            'clip' (treat overflow as the same as the last (or first) element).
            Default 'clip'. See numpy.take.

        Returns
        -------
        extrema : ndarray
            Boolean array of the same shape as `data` that is True at an extrema,
            False otherwise.

        See also
        --------
        argrelmax, argrelmin

        Examples
        --------
        >>> import numpy as np
        >>> testdata = np.array([1,2,3,2,1])
        >>> _boolrelextrema(testdata, np.greater, axis=0)
        array([False, False,  True, False, False], dtype=bool)

        """
        if (int(order) != order) or (order < 1):
            raise ValueError("Order must be an int >= 1")

        datalen = data.shape[axis]
        locs = np.arange(0, datalen)

        results = np.ones(data.shape, dtype=bool)
        main = data.take(locs, axis=axis, mode=mode)
        for shift in range(1, order + 1):
            plus = data.take(locs + shift, axis=axis, mode=mode)
            minus = data.take(locs - shift, axis=axis, mode=mode)
            results &= comparator(main, plus)
            results &= comparator(main, minus)
            if ~results.any():
                return results
        return np.nonzero(results)
