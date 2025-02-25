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
"""
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for analyzing and validating stocks
"""

import math
import warnings

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd

import pkscreener.classes.Utility as Utility
from pkscreener import Imports
from pkscreener.classes.Pktalib import pktalib

# from sklearn.preprocessing import StandardScaler
if Imports["scipy"]:
    from scipy.stats import linregress

from pkscreener.classes.ColorText import colorText
from pkscreener.classes.SuppressOutput import SuppressOutput


# Exception for only downloading stock data and not screening
class DownloadDataOnly(Exception):
    pass


# Exception for stocks which are not newly listed when screening only for Newly Listed
class NotNewlyListed(Exception):
    pass


# Exception for newly listed stocks with candle nos < daysToLookback
class StockDataNotAdequate(Exception):
    pass


# This Class contains methods for stock analysis and screening validation
class tools:
    def __init__(self, configManager, default_logger) -> None:
        self.configManager = configManager
        self.default_logger = default_logger
 
    # Find stocks that have broken through 52 week low.
    def find52WeekHighBreakout(self, data):
        # https://chartink.com/screener/52-week-low-breakout
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["High"].iloc[0]
        last1Week = data.head(one_week)
        last2Week = data.head(2*one_week)
        previousWeek = last2Week.tail(one_week)
        full52Week = data.head(50*one_week)
        last1WeekHigh = last1Week["High"].max()
        previousWeekHigh = previousWeek["High"].max()
        full52WeekHigh = full52Week["High"].max()
        return (recent >= full52WeekHigh) or (last1WeekHigh >= max(full52WeekHigh,last1WeekHigh)) or (last1WeekHigh >= previousWeekHigh >= max(full52WeekHigh,previousWeekHigh))
    

    # Find stocks that have broken through 52 week low.
    def find52WeekLowBreakout(self, data):
        # https://chartink.com/screener/52-week-low-breakout
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["Low"].iloc[0]
        last1Week = data.head(one_week)
        last2Week = data.head(2*one_week)
        previousWeek = last2Week.tail(one_week)
        full52Week = data.head(50*one_week)
        last1WeekLow = last1Week["Low"].min()
        previousWeekLow = previousWeek["Low"].min()
        full52WeekLow = full52Week["Low"].min()
        return (recent <= full52WeekLow) or (last1WeekLow <= min(full52WeekLow,last1WeekLow)) or (last1WeekLow <= previousWeekLow <= min(full52WeekLow,previousWeekLow))
    
        # Find stocks that have broken through 52 week low.
    def find10DaysLowBreakout(self, data):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["Low"].iloc[0]
        last1Week = data.head(one_week)
        last2Week = data.head(2*one_week)
        previousWeek = last2Week.tail(one_week)
        last1WeekLow = last1Week["Low"].min()
        previousWeekLow = previousWeek["Low"].min()
        return (recent <= min(previousWeekLow,last1WeekLow)) and (last1WeekLow <= previousWeekLow)
    
        # Find stocks that have broken through 52 week low.
    def findAroonBullishCrossover(self, data):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        period = 14
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        aroondf = pktalib.Aroon(data['High'],data['Low'], period)
        recent = aroondf.tail(1)
        up = recent[f"AROONU_{period}"].iloc[0]
        down = recent[f"AROOND_{period}"].iloc[0]
        return up > down
    
    # Find accurate breakout value
    def findBreakout(self, data, screenDict, saveDict, daysToLookback):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        data = data[1:]
        hs = round(data.describe()["High"]["max"], 2)
        hc = round(data.describe()["Close"]["max"], 2)
        rc = round(recent["Close"].iloc[0], 2)
        if np.isnan(hc) or np.isnan(hs):
            saveDict["Breakout"] = "BO: Unknown"
            screenDict["Breakout"] = (
                colorText.BOLD + colorText.WARN + "BO: Unknown" + colorText.END
            )
            self.default_logger.info(
                f'For Stock:{saveDict["Stock"]}, the breakout is unknown because max-high ({hs}) or max-close ({hc}) are not defined.'
            )
            return False
        if hs > hc:
            if (hs - hc) <= (hs * 2 / 100):
                saveDict["Breakout"] = "BO: " + str(hc)
                if rc >= hc:
                    screenDict["Breakout"] = (
                        colorText.BOLD
                        + colorText.GREEN
                        + "BO: "
                        + str(hc)
                        + " R: "
                        + str(hs)
                        + colorText.END
                    )
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, has a breakout because max-high ({hs}) >= max-close ({hc})'
                    )
                    return True and self.getCandleType(recent)
                self.default_logger.info(
                    f'Stock:{saveDict["Stock"]}, does not have a breakout yet because max-high ({hs}) < max-close ({hc})'
                )
                screenDict["Breakout"] = (
                    colorText.BOLD
                    + colorText.FAIL
                    + "BO: "
                    + str(hc)
                    + " R: "
                    + str(hs)
                    + colorText.END
                )
                return False
            noOfHigherShadows = len(data[data.High > hc])
            if daysToLookback / noOfHigherShadows <= 3:
                saveDict["Breakout"] = "BO: " + str(hs)
                if rc >= hs:
                    screenDict["Breakout"] = (
                        colorText.BOLD
                        + colorText.GREEN
                        + "BO: "
                        + str(hs)
                        + colorText.END
                    )
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({rc}) >= max-high ({hs})'
                    )
                    return True and self.getCandleType(recent)
                self.default_logger.info(
                    f'Stock:{saveDict["Stock"]}, does not have a breakout yet because recent-close ({rc}) < max-high ({hs})'
                )
                screenDict["Breakout"] = (
                    colorText.BOLD + colorText.FAIL + "BO: " + str(hs) + colorText.END
                )
                return False
            saveDict["Breakout"] = "BO: " + str(hc) + ", R: " + str(hs)
            if rc >= hc:
                self.default_logger.info(
                    f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({rc}) >= max-close ({hc})'
                )
                screenDict["Breakout"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + "BO: "
                    + str(hc)
                    + " R: "
                    + str(hs)
                    + colorText.END
                )
                return True and self.getCandleType(recent)
            self.default_logger.info(
                f'Stock:{saveDict["Stock"]}, does not have a breakout yet because recent-close ({rc}) < max-high ({hs})'
            )
            screenDict["Breakout"] = (
                colorText.BOLD
                + colorText.FAIL
                + "BO: "
                + str(hc)
                + " R: "
                + str(hs)
                + colorText.END
            )
            return False
        else:
            saveDict["Breakout"] = "BO: " + str(hc)
            if rc >= hc:
                self.default_logger.info(
                    f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({rc}) >= max-close ({hc})'
                )
                screenDict["Breakout"] = (
                    colorText.BOLD + colorText.GREEN + "BO: " + str(hc) + colorText.END
                )
                return True and self.getCandleType(recent)
            self.default_logger.info(
                f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({rc}) < max-close ({hc})'
            )
            screenDict["Breakout"] = (
                colorText.BOLD + colorText.FAIL + "BO: " + str(hc) + colorText.END
            )
            return False

    # Find stocks that are bullish intraday: RSI crosses 55, Macd Histogram positive, price above EMA 10
    def findBullishIntradayRSIMACD(self, data):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["RSI12"] = pktalib.RSI(data["Close"], 12)
        data["EMA10"] = pktalib.EMA(data["Close"], 10)
        data["EMA200"] = pktalib.EMA(data["Close"], 200)
        macd = pktalib.MACD(data["Close"], 10, 18, 9)[2].tail(1)
        recent = data.tail(1)
        cond1 = recent["RSI12"].iloc[0] > 55
        cond2 = cond1 and (macd.iloc[:1][0] > 0)
        cond3 = cond2 and (recent["Close"].iloc[0] > recent["EMA10"].iloc[0])
        cond4 = cond3 and (recent["Close"].iloc[0] > recent["EMA200"].iloc[0])
        return cond4

    def findNR4Day(self, data):
        # https://chartink.com/screener/nr4-daily-today
        if data.tail(1)["Volume"].iloc[0] <= 50000:
            return False
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["SMA10"] = pktalib.SMA(data["Close"], 10)
        data["SMA50"] = pktalib.SMA(data["Close"], 50)
        data["SMA200"] = pktalib.SMA(data["Close"], 200)
        recent = data.tail(5)
        recent = recent[::-1]
        cond1 = (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[1] - recent["Low"].iloc[1]
        )
        cond2 = cond1 and (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[2] - recent["Low"].iloc[2]
        )
        cond3 = cond2 and (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[3] - recent["Low"].iloc[3]
        )
        cond4 = cond3 and (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[4] - recent["Low"].iloc[4]
        )
        cond5 = cond4 and (recent["SMA10"].iloc[0] > recent["SMA50"].iloc[0])
        cond6 = cond5 and (recent["SMA50"].iloc[0] > recent["SMA200"].iloc[0])
        return cond6

    # Find stock reversing at given MA
    def findReversalMA(self, data, screenDict, saveDict, maLength, percentage=0.02):
        maRange = [10,20,50,200]
        results = []
        hasReversals = False
        data = data[::-1]
        for maLength in maRange:
            dataCopy = data
            if self.configManager.useEMA:
                maRev = pktalib.EMA(dataCopy["Close"], timeperiod=maLength)
            else:
                maRev = pktalib.MA(dataCopy["Close"], timeperiod=maLength)
            try:
                dataCopy.drop('maRev', axis=1, inplace=True, errors='ignore')
            except Exception:
                pass
            dataCopy.insert(len(dataCopy.columns), "maRev", maRev)
            dataCopy = dataCopy[::-1].head(3)
            if (
                dataCopy.equals(
                    dataCopy[
                        (dataCopy.Close >= (dataCopy.maRev - (dataCopy.maRev * percentage)))
                        & (dataCopy.Close <= (dataCopy.maRev + (dataCopy.maRev * percentage)))
                    ]
                )
                and dataCopy.head(1)["Close"].iloc[0] >= dataCopy.head(1)["maRev"].iloc[0]
            ):
                hasReversals = True
                results.append(str(maLength))
        if hasReversals:
            screenDict["MA-Signal"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + f"Reversal-[{','.join(results)}]MA"
                    + colorText.END
                )
            saveDict["MA-Signal"] = f"Reversal-[{','.join(results)}]MA"
        return hasReversals

    # Find out trend for days to lookback
    def findTrend(self, data, screenDict, saveDict, daysToLookback=None, stockName=""):
        if daysToLookback is None:
            daysToLookback = self.configManager.daysToLookback
        data = data.head(daysToLookback)
        data = data[::-1]
        data = data.set_index(np.arange(len(data)))
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        try:
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                data["tops"] = data["Close"].iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["Close"]), np.greater_equal, order=1
                        )[0]
                    )
                ]
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)

            try:
                if len(data) < daysToLookback:
                    raise StockDataNotAdequate
                slope, c = np.polyfit(
                    data.index[data.tops > 0], data["tops"][data.tops > 0], 1
                )
            except Exception as e:
                self.default_logger.debug(e, exc_info=True)
                slope, _ = 0, 0
            angle = np.rad2deg(np.arctan(slope))
            if angle == 0:
                screenDict["Trend"] = (
                    colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = "Unknown"
            elif angle <= 30 and angle >= -30:
                screenDict["Trend"] = (
                    colorText.BOLD + colorText.WARN + "Sideways" + colorText.END
                )
                saveDict["Trend"] = "Sideways"
            elif angle >= 30 and angle < 61:
                screenDict["Trend"] = (
                    colorText.BOLD + colorText.GREEN + "Weak Up" + colorText.END
                )
                saveDict["Trend"] = "Weak Up"
            elif angle >= 60:
                screenDict["Trend"] = (
                    colorText.BOLD + colorText.GREEN + "Strong Up" + colorText.END
                )
                saveDict["Trend"] = "Strong Up"
            elif angle <= -30 and angle > -61:
                screenDict["Trend"] = (
                    colorText.BOLD + colorText.FAIL + "Weak Down" + colorText.END
                )
                saveDict["Trend"] = "Weak Down"
            elif angle <= -60:
                screenDict["Trend"] = (
                    colorText.BOLD + colorText.FAIL + "Strong Down" + colorText.END
                )
                saveDict["Trend"] = "Strong Down"
        except np.linalg.LinAlgError as e:
            self.default_logger.debug(e, exc_info=True)
            screenDict["Trend"] = (
                colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
            )
            saveDict["Trend"] = "Unknown"
        return saveDict["Trend"]

    # Find stocks approching to long term trendlines
    def findTrendlines(self, data, screenDict, saveDict, percentage=0.05):
        period = int("".join(c for c in self.configManager.period if c.isdigit()))
        if len(data) < period:
            return False

        data = data[::-1]
        data["Number"] = np.arange(len(data)) + 1
        data_low = data.copy()
        points = 30

        """ Ignoring the Resitance for long-term purpose
        while len(data_high) > points:
            slope, intercept, r_value, p_value, std_err = linregress(x=data_high['Number'], y=data_high['High'])
            data_high = data_high.loc[data_high['High'] > slope * data_high['Number'] + intercept]
        slope, intercept, r_value, p_value, std_err = linregress(x=data_high['Number'], y=data_high['Close'])
        data['Resistance'] = slope * data['Number'] + intercept
        """

        while len(data_low) > points:
            try:
                slope, intercept, r_value, p_value, std_err = linregress(
                    x=data_low["Number"], y=data_low["Low"]
                )
            except Exception as e:
                self.default_logger.debug(e, exc_info=True)
                continue
            data_low = data_low.loc[
                data_low["Low"] < slope * data_low["Number"] + intercept
            ]

        slope, intercept, r_value, p_value, std_err = linregress(
            x=data_low["Number"], y=data_low["Close"]
        )
        data["Support"] = slope * data["Number"] + intercept
        now = data.tail(1)

        limit_upper = now["Support"].iloc[0] + (now["Support"].iloc[0] * percentage)
        limit_lower = now["Support"].iloc[0] - (now["Support"].iloc[0] * percentage)

        if limit_lower < now["Close"].iloc[0] < limit_upper and slope > 0.15:
            screenDict["Pattern"] = (
                colorText.BOLD + colorText.GREEN + "Trendline-Support" + colorText.END
            )
            saveDict["Pattern"] = "Trendline-Support"
            return True

        """ Plots for debugging
        import matplotlib.pyplot as plt
        fig, ax1 = plt.subplots(figsize=(15,10))
        color = 'tab:green'
        xdate = [x.date() for x in data.index]
        ax1.set_xlabel('Date', color=color)
        ax1.plot(xdate, data.Close, label="close", color=color)
        ax1.tick_params(axis='x', labelcolor=color)

        ax2 = ax1.twiny() # ax2 and ax1 will have common y axis and different x axis, twiny
        ax2.plot(data.Number, data.Resistance, label="Res")
        ax2.plot(data.Number, data.Support, label="Sup")

        plt.legend()
        plt.grid()
        plt.show()
        """
        return False

    # Private method to find candle type
    # True = Bullish, False = Bearish
    def getCandleType(self, dailyData):
        return bool(dailyData["Close"].iloc[0] >= dailyData["Open"].iloc[0])

    def getNiftyPrediction(self, data):
        import warnings

        warnings.filterwarnings("ignore")
        model, pkl = Utility.tools.getNiftyModel()
        if model is None or pkl is None:
            return 0, "Unknown", "Unknown"
        with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
            data = data[pkl["columns"]]
            ### v2 Preprocessing
            data["High"] = data["High"].pct_change() * 100
            data["Low"] = data["Low"].pct_change() * 100
            data["Open"] = data["Open"].pct_change() * 100
            data["Close"] = data["Close"].pct_change() * 100
            data = data.iloc[-1]
            ###
            data = pkl["scaler"].transform([data])
            pred = model.predict(data)[0]
        if pred > 0.5:
            outText = "BEARISH"
            out = (
                colorText.BOLD
                + colorText.FAIL
                + outText
                + colorText.END
                + colorText.BOLD
            )
            sug = "Hold your Short position!"
        else:
            outText = "BULLISH"
            out = (
                colorText.BOLD
                + colorText.GREEN
                + outText
                + colorText.END
                + colorText.BOLD
            )
            sug = "Stay Bullish!"
        if not Utility.tools.isClosingHour():
            print(
                colorText.BOLD
                + colorText.WARN
                + "Note: The AI prediction should be executed After 3 PM or Near to Closing time as the Prediction Accuracy is based on the Closing price!"
                + colorText.END
            )
        predictionText = "Market may Open {} next day! {}".format(out, sug)
        strengthText = "Probability/Strength of Prediction = {}%".format(
            Utility.tools.getSigmoidConfidence(pred[0])
        )
        print(
            colorText.BOLD
            + colorText.BLUE
            + "\n"
            + "[+] Nifty AI Prediction -> "
            + colorText.END
            + colorText.BOLD
            + predictionText
            + colorText.END
        )
        print(
            colorText.BOLD
            + colorText.BLUE
            + "\n"
            + "[+] Nifty AI Prediction -> "
            + colorText.END
            + strengthText
        )

        return pred, predictionText.replace(out, outText), strengthText

    def monitorFiveEma(
        self, fetcher, result_df, last_signal, risk_reward=3
    ):
        col_names = ["High", "Low", "Close", "5EMA"]
        data_list = ["nifty_buy", "banknifty_buy", "nifty_sell", "banknifty_sell"]

        data_tuple = fetcher.fetchFiveEmaData()
        for cnt in range(len(data_tuple)):
            d = data_tuple[cnt]
            d["5EMA"] = pktalib.EMA(d["Close"], timeperiod=5)
            d = d[col_names]
            d = d.dropna().round(2)

            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                if "sell" in data_list[cnt]:
                    streched = d[(d.Low > d["5EMA"]) & (d.Low - d["5EMA"] > 0.5)]
                    streched["SL"] = streched.High
                    validate = d[
                        (d.Low.shift(1) > d["5EMA"].shift(1))
                        & (d.Low.shift(1) - d["5EMA"].shift(1) > 0.5)
                    ]
                    old_index = validate.index
                else:
                    mask = (d.High < d["5EMA"]) & (d["5EMA"] - d.High > 0.5)  # Buy
                    streched = d[mask]
                    streched["SL"] = streched.Low
                    validate = d.loc[mask.shift(1).fillna(False)]
                    old_index = validate.index
            tgt = pd.DataFrame(
                (
                    validate.Close.reset_index(drop=True)
                    - (
                        (
                            streched.SL.reset_index(drop=True)
                            - validate.Close.reset_index(drop=True)
                        )
                        * risk_reward
                    )
                ),
                columns=["Target"],
            )
            validate = pd.concat(
                [
                    validate.reset_index(drop=True),
                    streched["SL"].reset_index(drop=True),
                    tgt,
                ],
                axis=1,
            )
            validate = validate.tail(len(old_index))
            validate = validate.set_index(old_index)
            if "sell" in data_list[cnt]:
                final = validate[validate.Close < validate["5EMA"]].tail(1)
            else:
                final = validate[validate.Close > validate["5EMA"]].tail(1)

            if data_list[cnt] not in last_signal:
                last_signal[data_list[cnt]] = final
            elif data_list[cnt] in last_signal:
                try:
                    condition = last_signal[data_list[cnt]][0]["SL"][0]
                except KeyError as e:
                    self.default_logger.debug(e, exc_info=True)
                    condition = last_signal[data_list[cnt]]["SL"][0]
                # if last_signal[data_list[cnt]] is not final:          # Debug - Shows all conditions
                if len(final["SL"]) > 0 and condition != final["SL"].iloc[0]:
                    # Do something with results
                    try:
                        result_df = pd.concat(
                            [
                                result_df,
                                pd.DataFrame(
                                    [
                                        [
                                            colorText.BLUE
                                            + str(final.index[0])
                                            + colorText.END,
                                            colorText.BOLD
                                            + colorText.WARN
                                            + data_list[cnt].split("_")[0].upper()
                                            + colorText.END,
                                            (
                                                colorText.BOLD
                                                + colorText.FAIL
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            )
                                            if "sell" in data_list[cnt]
                                            else (
                                                colorText.BOLD
                                                + colorText.GREEN
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            ),
                                            colorText.FAIL
                                            + str(final.SL[0])
                                            + colorText.END,
                                            colorText.GREEN
                                            + str(final.Target[0])
                                            + colorText.END,
                                            f"1:{risk_reward}",
                                        ]
                                    ],
                                    columns=result_df.columns,
                                ),
                            ],
                            axis=0,
                        )
                        result_df.reset_index(drop=True, inplace=True)
                    except Exception as e:
                        self.default_logger.debug(e, exc_info=True)
                        pass
                    # Then update
                    last_signal[data_list[cnt]] = [final]
        if result_df is not None:
            result_df.drop_duplicates(keep="last", inplace=True)
            result_df.sort_values(by="Time", inplace=True)
        return result_df[::-1]

    # Preprocess the acquired data
    def preprocessData(self, data, daysToLookback=None):
        self.default_logger.info(f"Preprocessing data:\n{data.head(1)}\n")
        if daysToLookback is None:
            daysToLookback = self.configManager.daysToLookback
        if self.configManager.useEMA:
            sma = pktalib.EMA(data["Close"], timeperiod=50)
            lma = pktalib.EMA(data["Close"], timeperiod=200)
            ssma = pktalib.EMA(data["Close"], timeperiod=9)
            data.insert(6, "SMA", sma)
            data.insert(7, "LMA", lma)
            data.insert(8, "SSMA", ssma)
        else:
            sma = data.rolling(window=50).mean()
            lma = data.rolling(window=200).mean()
            ssma = data.rolling(window=9).mean()
            data.insert(6, "SMA", sma["Close"])
            data.insert(7, "LMA", lma["Close"])
            data.insert(8, "SSMA", ssma["Close"])
        vol = data.rolling(window=20).mean()
        rsi = pktalib.RSI(data["Close"], timeperiod=14)
        data.insert(9, "VolMA", vol["Volume"])
        data.insert(10, "RSI", rsi)
        cci = pktalib.CCI(data["High"], data["Low"], data["Close"], timeperiod=14)
        data.insert(11, "CCI", cci)
        # len(data["Close"])
        fastk, fastd = pktalib.STOCHRSI(
            data["Close"], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0
        )
        data.insert(12, "FASTK", fastk)
        data.insert(13, "FASTD", fastd)
        data = data[::-1]  # Reverse the dataframe
        # data = data.fillna(0)
        # data = data.replace([np.inf, -np.inf], 0)
        fullData = data
        trimmedData = data.head(daysToLookback)
        return (fullData, trimmedData)

    # Validate if the stock is bullish in the short term
    def validate15MinutePriceVolumeBreakout(self, data):
        # https://chartink.com/screener/15-min-price-volume-breakout
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["SMA20"] = pktalib.SMA(data["Close"], 20)
        data["SMA20V"] = pktalib.SMA(data["Volume"], 20)
        data = data[
            ::-1
        ]  # Reverse the dataframe so that it's the most recent date first
        recent = data.head(3)
        cond1 = recent["Close"].iloc[0] > recent["Close"].iloc[1]
        cond2 = cond1 and (recent["Close"].iloc[0] > recent["SMA20"].iloc[0])
        cond3 = cond2 and (recent["Close"].iloc[1] > recent["High"].iloc[2])
        cond4 = cond3 and (recent["Volume"].iloc[0] > recent["SMA20V"].iloc[0])
        cond5 = cond4 and (recent["Volume"].iloc[1] > recent["SMA20V"].iloc[0])
        return cond5

    def validateBullishForTomorrow(self, data):
        # https://chartink.com/screener/bullish-for-tomorrow
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macdLine = pktalib.MACD(data["Close"], 12, 26, 9)[0].tail(3)
        macdSignal = pktalib.MACD(data["Close"], 12, 26, 9)[1].tail(3)
        macdHist = pktalib.MACD(data["Close"], 12, 26, 9)[2].tail(3)
        
        return (
                (macdHist.iloc[:1].iloc[0] < macdHist.iloc[:2].iloc[1]) and
                (macdHist.iloc[:3].iloc[2] > macdHist.iloc[:2].iloc[1]) and
                ((macdLine.iloc[:3].iloc[2] - macdSignal.iloc[:3].iloc[2]) - (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1]) >= 0.4) and
                ((macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1]) - (macdLine.iloc[:1].iloc[0] - macdSignal.iloc[:1].iloc[0]) <= 0.2) and
                (macdLine.iloc[:3].iloc[2] > macdSignal.iloc[:3].iloc[2]) and
                ((macdLine.iloc[:3].iloc[2] - macdSignal.iloc[:3].iloc[2]) - (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1]) < 1)
                )
    
    # validate if CCI is within given range
    def validateCCI(self, data, screenDict, saveDict, minCCI, maxCCI):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        cci = int(data.head(1)["CCI"].iloc[0])
        saveDict["CCI"] = cci
        if (cci <= minCCI or cci >= maxCCI) and ("Up" in saveDict["Trend"]):
            if (cci <= minCCI) or cci >= maxCCI:
                screenDict["CCI"] = (
                    colorText.BOLD + colorText.GREEN + str(cci) + colorText.END
                )
            else:
                screenDict["CCI"] = (
                    colorText.BOLD + colorText.FAIL + str(cci) + colorText.END
                )
            return True
        screenDict["CCI"] = colorText.BOLD + colorText.FAIL + str(cci) + colorText.END
        return False

    # Find Conflucence
    def validateConfluence(self, stock, data, screenDict, saveDict, percentage=0.1):
        recent = data.head(1)
        if abs(recent["SMA"].iloc[0] - recent["LMA"].iloc[0]) <= (recent["SMA"].iloc[0] * percentage):
            difference = round(
                abs(recent["SMA"].iloc[0] - recent["LMA"].iloc[0]) / recent["Close"].iloc[0] * 100, 2
            )
            if recent["SMA"].iloc[0] >= recent["LMA"].iloc[0]:
                screenDict["MA-Signal"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + f"Confluence ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = f"Confluence ({difference}%)"
            else:
                screenDict["MA-Signal"] = (
                    colorText.BOLD
                    + colorText.FAIL
                    + f"Confluence ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = f"Confluence ({difference}%)"
            return True
        return False

    # Validate if share prices are consolidating
    def validateConsolidation(self, data, screenDict, saveDict, percentage=10):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        hc = data.describe()["Close"]["max"]
        lc = data.describe()["Close"]["min"]
        if (hc - lc) <= (hc * percentage / 100) and (hc - lc != 0):
            screenDict["Consol."] = (
                colorText.BOLD
                + colorText.GREEN
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        else:
            screenDict["Consol."] = (
                colorText.BOLD
                + colorText.FAIL
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        saveDict["Consol."] = f'Range:{str(round((abs((hc-lc)/hc)*100),1))+"%"}'
        return round((abs((hc - lc) / hc) * 100), 1)

    # Validate 'Inside Bar' structure for recent days
    def validateInsideBar(
        self, data, screenDict, saveDict, chartPattern=1, daysToLookback=5
    ):
        orgData = data
        for i in range(daysToLookback, round(daysToLookback * 0.5) - 1, -1):
            if i == 2:
                return 0  # Exit if only last 2 candles are left
            if chartPattern == 1:
                if "Up" in saveDict["Trend"] and (
                    "Bull" in saveDict["MA-Signal"]
                    or "Support" in saveDict["MA-Signal"]
                ):
                    data = orgData.head(i)
                    refCandle = data.tail(1)
                    if (
                        (len(data.High[data.High > refCandle.High.item()]) == 0)
                        and (len(data.Low[data.Low < refCandle.Low.item()]) == 0)
                        and (len(data.Open[data.Open > refCandle.High.item()]) == 0)
                        and (len(data.Close[data.Close < refCandle.Low.item()]) == 0)
                    ):
                        screenDict["Pattern"] = (
                            colorText.BOLD
                            + colorText.WARN
                            + ("Inside Bar (%d)" % i)
                            + colorText.END
                        )
                        saveDict["Pattern"] = "Inside Bar (%d)" % i
                        return i
                else:
                    return 0
            else:
                if "Down" in saveDict["Trend"] and (
                    "Bear" in saveDict["MA-Signal"] or "Resist" in saveDict["MA-Signal"]
                ):
                    data = orgData.head(i)
                    refCandle = data.tail(1)
                    if (
                        (len(data.High[data.High > refCandle.High.item()]) == 0)
                        and (len(data.Low[data.Low < refCandle.Low.item()]) == 0)
                        and (len(data.Open[data.Open > refCandle.High.item()]) == 0)
                        and (len(data.Close[data.Close < refCandle.Low.item()]) == 0)
                    ):
                        screenDict["Pattern"] = (
                            colorText.BOLD
                            + colorText.WARN
                            + ("Inside Bar (%d)" % i)
                            + colorText.END
                        )
                        saveDict["Pattern"] = "Inside Bar (%d)" % i
                        return i
                else:
                    return 0
        return 0

    # Find IPO base
    def validateIpoBase(self, stock, data, screenDict, saveDict, percentage=0.3):
        listingPrice = data[::-1].head(1)["Open"].iloc[0]
        currentPrice = data.head(1)["Close"].iloc[0]
        ATH = data.describe()["High"]["max"]
        if ATH > (listingPrice + (listingPrice * percentage)):
            return False
        away = round(((currentPrice - listingPrice) / listingPrice) * 100, 1)
        if (
            (listingPrice - (listingPrice * percentage))
            <= currentPrice
            <= (listingPrice + (listingPrice * percentage))
        ):
            if away > 0:
                screenDict["Pattern"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + f"IPO Base ({away} %)"
                    + colorText.END
                )
            else:
                screenDict["Pattern"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + "IPO Base "
                    + colorText.FAIL
                    + f"({away} %)"
                    + colorText.END
                )
            saveDict["Pattern"] = f"IPO Base ({away} %)"
            return True
        return False

    # Validate if recent volume is lowest of last 'N' Days
    def validateLowestVolume(self, data, daysForLowestVolume):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        if daysForLowestVolume is None:
            daysForLowestVolume = 30
        data = data.head(daysForLowestVolume)
        recent = data.head(1)
        if (recent["Volume"].iloc[0] <= data.describe()["Volume"]["min"]) and recent[
            "Volume"
        ][0] != np.nan:
            return True
        return False

    # Validate LTP within limits
    def validateLTP(self, data, screenDict, saveDict, minLTP=None, maxLTP=None):
        if minLTP is None:
            minLTP = self.configManager.minLTP
        if maxLTP is None:
            maxLTP = self.configManager.maxLTP
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)

        pct_change = (data[::-1]["Close"].pct_change() * 100).iloc[-1]
        pct_save = "%.1f%%" % pct_change
        if pct_change > 0.2:
            pct_change = colorText.GREEN + ("%.1f%%" % pct_change) + colorText.END
        elif pct_change < -0.2:
            pct_change = colorText.FAIL + ("%.1f%%" % pct_change) + colorText.END
        else:
            pct_change = colorText.WARN + ("%.1f%%" % pct_change) + colorText.END
        saveDict["%Chng"] = pct_save
        screenDict["%Chng"] = pct_change
        ltp = round(recent["Close"].iloc[0], 2)
        verifyStageTwo = True
        if self.configManager.stageTwo and len(data) > 250:
            yearlyLow = data.head(250).min()["Close"]
            yearlyHigh = data.head(250).max()["Close"]
            if ltp < (2 * yearlyLow) or ltp < (0.75 * yearlyHigh):
                verifyStageTwo = False
        if ltp >= minLTP and ltp <= maxLTP and verifyStageTwo:
            saveDict["LTP"] = str((" %.2f" % ltp))
            screenDict["LTP"] = colorText.GREEN + ("%.2f" % ltp) + colorText.END
            return True, verifyStageTwo
        screenDict["LTP"] = colorText.FAIL + ("%.2f" % ltp) + colorText.END
        saveDict["LTP"] = str((" %.2f" % ltp))
        return False, verifyStageTwo

    # Find stocks that are bearish intraday: Macd Histogram negative
    def validateMACDHistogramBelow0(self, data):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macd = pktalib.MACD(data["Close"], 12, 26, 9)[2].tail(1)
        return macd.iloc[:1][0] < 0
    
    # Find if stock gaining bullish momentum
    def validateMomentum(self, data, screenDict, saveDict):
        try:
            data = data.head(3)
            for row in data.iterrows():
                # All 3 candles should be Green and NOT Circuits
                yc = row[1]["Close"].item()
                yo = row[1]["Open"].item()
                if yc <= yo:
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because yesterday-close ({yc}) <= yesterday-open ({yo})'
                    )
                    return False
            openDesc = data.sort_values(by=["Open"], ascending=False)
            closeDesc = data.sort_values(by=["Close"], ascending=False)
            volDesc = data.sort_values(by=["Volume"], ascending=False)
            try:
                if (
                    data.equals(openDesc)
                    and data.equals(closeDesc)
                    and data.equals(volDesc)
                ):
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, open,close and volume equal from day before yesterday. A potential momentum-gainer!'
                    )
                    to = data["Open"].iloc[0]
                    yc = data["Close"].iloc[1]
                    yo = data["Open"].iloc[1]
                    dyc = data["Close"].iloc[2]
                    if (to >= yc) and (yo >= dyc):
                        self.default_logger.info(
                            f'Stock:{saveDict["Stock"]}, is a momentum-gainer because today-open ({to}) >= yesterday-close ({yc}) and yesterday-open({yo}) >= day-before-close({dyc})'
                        )
                        screenDict["Pattern"] = (
                            colorText.BOLD
                            + colorText.GREEN
                            + "Momentum Gainer"
                            + colorText.END
                        )
                        saveDict["Pattern"] = "Momentum Gainer"
                        return True
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because either today-open ({to}) < yesterday-close ({yc}) or yesterday-open({yo}) < day-before-close({dyc})'
                    )
            except IndexError as e:
                self.default_logger.debug(e, exc_info=True)
                pass
            return False
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            return False

    # Validate Moving averages and look for buy/sell signals
    def validateMovingAverages(self, data, screenDict, saveDict, maRange=2.5):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        if (
            recent["SMA"].iloc[0] > recent["LMA"].iloc[0]
            and recent["Close"].iloc[0] > recent["SMA"].iloc[0]
        ):
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.GREEN + "Bullish" + colorText.END
            )
            saveDict["MA-Signal"] = "Bullish"
        elif recent["SMA"].iloc[0] < recent["LMA"].iloc[0]:
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.FAIL + "Bearish" + colorText.END
            )
            saveDict["MA-Signal"] = "Bearish"
        elif recent["SMA"].iloc[0] == 0:
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
            )
            saveDict["MA-Signal"] = "Unknown"
        else:
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.WARN + "Neutral" + colorText.END
            )
            saveDict["MA-Signal"] = "Neutral"

        smaDev = data["SMA"].iloc[0] * maRange / 100
        lmaDev = data["LMA"].iloc[0] * maRange / 100
        open, high, low, close, sma, lma = (
            data["Open"].iloc[0],
            data["High"].iloc[0],
            data["Low"].iloc[0],
            data["Close"].iloc[0],
            data["SMA"].iloc[0],
            data["LMA"].iloc[0],
        )
        maReversal = 0
        # Taking Support 50
        if close > sma and low <= (sma + smaDev):
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.GREEN + "50MA-Support" + colorText.END
            )
            saveDict["MA-Signal"] = "50MA-Support"
            maReversal = 1
        # Validating Resistance 50
        elif close < sma and high >= (sma - smaDev):
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.FAIL + "50MA-Resist" + colorText.END
            )
            saveDict["MA-Signal"] = "50MA-Resist"
            maReversal = -1
        # Taking Support 200
        elif close > lma and low <= (lma + lmaDev):
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.GREEN + "200MA-Support" + colorText.END
            )
            saveDict["MA-Signal"] = "200MA-Support"
            maReversal = 1
        # Validating Resistance 200
        elif close < lma and high >= (lma - lmaDev):
            screenDict["MA-Signal"] = (
                colorText.BOLD + colorText.FAIL + "200MA-Resist" + colorText.END
            )
            saveDict["MA-Signal"] = "200MA-Resist"
            maReversal = -1
        # For a Bullish Candle
        if self.getCandleType(data):
            # Crossing up 50
            if open < sma and close > sma:
                screenDict["MA-Signal"] = (
                    colorText.BOLD + colorText.GREEN + "BullCross-50MA" + colorText.END
                )
                saveDict["MA-Signal"] = "BullCross-50MA"
                maReversal = 1
            # Crossing up 200
            elif open < lma and close > lma:
                screenDict["MA-Signal"] = (
                    colorText.BOLD + colorText.GREEN + "BullCross-200MA" + colorText.END
                )
                saveDict["MA-Signal"] = "BullCross-200MA"
                maReversal = 1
        # For a Bearish Candle
        elif not self.getCandleType(data):
            # Crossing down 50
            if open > sma and close < sma:
                screenDict["MA-Signal"] = (
                    colorText.BOLD + colorText.FAIL + "BearCross-50MA" + colorText.END
                )
                saveDict["MA-Signal"] = "BearCross-50MA"
                maReversal = -1
            # Crossing up 200
            elif open > lma and close < lma:
                screenDict["MA-Signal"] = (
                    colorText.BOLD + colorText.FAIL + "BearCross-200MA" + colorText.END
                )
                saveDict["MA-Signal"] = "BearCross-200MA"
                maReversal = -1
        return maReversal

    # Find NRx range for Reversal
    def validateNarrowRange(self, data, screenDict, saveDict, nr=4):
        if Utility.tools.isTradingTime():
            rangeData = data.head(nr + 1)[1:]
            now_candle = data.head(1)
            rangeData["Range"] = abs(rangeData["Close"] - rangeData["Open"])
            recent = rangeData.head(1)
            if recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]:
                if (
                    self.getCandleType(recent)
                    and now_candle["Close"].iloc[0] >= recent["Close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        colorText.BOLD + colorText.GREEN + f"Buy-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = f"Buy-NR{nr}"
                    return True
                elif (
                    not self.getCandleType(recent)
                    and now_candle["Close"].iloc[0] <= recent["Close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        colorText.BOLD + colorText.FAIL + f"Sell-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = f"Sell-NR{nr}"
                    return True
            return False
        else:
            rangeData = data.head(nr)
            rangeData["Range"] = abs(rangeData["Close"] - rangeData["Open"])
            recent = rangeData.head(1)
            if recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]:
                screenDict["Pattern"] = (
                    colorText.BOLD + colorText.GREEN + f"NR{nr}" + colorText.END
                )
                saveDict["Pattern"] = f"NR{nr}"
                return True
            return False

    # Find if stock is newly listed
    def validateNewlyListed(self, data, daysToLookback):
        daysToLookback = int(daysToLookback[:-1])
        recent = data.head(1)
        if len(data) < daysToLookback and (
            recent["Close"].iloc[0] != np.nan and recent["Close"].iloc[0] > 0
        ):
            return True
        return False

    # Validate if the stock prices are at least rising by 2% for the last 3 sessions
    def validatePriceRisingByAtLeast2Percent(self, data, screenDict, saveDict):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data.head(4)
        day0 = data.iloc[0]["Close"].item()
        dayMinus1 = data.iloc[1]["Close"].item()
        dayMinus2 = data.iloc[2]["Close"].item()
        dayMinus3 = data.iloc[3]["Close"].item()
        percent3 = round((dayMinus2 - dayMinus3) * 100 / dayMinus3, 2)
        percent2 = round((dayMinus1 - dayMinus2) * 100 / dayMinus2, 2)
        percent1 = round((day0 - dayMinus1) * 100 / dayMinus1, 2)

        if percent1 >= 2 and percent2 >= 2 and percent3 >= 2:
            pct_change_text = (
                (" (%.1f%%," % percent1)
                + (" %.1f%%," % percent2)
                + (" %.1f%%)" % percent3)
            )
            pct_change = colorText.GREEN + pct_change_text + colorText.END
            screenDict["LTP"] = (
                colorText.GREEN + ("%.2f" % round(day0, 2)) + pct_change + colorText.END
            )
            saveDict["LTP"] = ("%.2f" % round(day0, 2)) + pct_change_text
            return True and self.getCandleType(data.head(1))
        return False

    # validate if RSI is within given range
    def validateRSI(self, data, screenDict, saveDict, minRSI, maxRSI):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        rsi = int(data.head(1)["RSI"].iloc[0])
        saveDict["RSI"] = rsi
        #https://chartink.com/screener/rsi-screening
        if (rsi >= minRSI and rsi <= maxRSI) or (rsi <= 71 and rsi >= 67):
            screenDict["RSI"] = (
                colorText.BOLD + colorText.GREEN + str(rsi) + colorText.END
            )
            return True
        screenDict["RSI"] = colorText.BOLD + colorText.FAIL + str(rsi) + colorText.END
        return False

    # Validate if the stock is bullish in the short term
    def validateShortTermBullish(self, data, screenDict, saveDict):
        # https://chartink.com/screener/short-term-bullish
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        fk = 0 if len(data) < 3 else np.round(data["FASTK"].iloc[2], 5)
        # Reverse the dataframe for ichimoku calculations with date in ascending order
        df_new = data[::-1]
        try:
            df_ichi = df_new.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )
            ichi = pktalib.ichimoku(df_ichi, 9, 26, 52, 26)
            if ichi is None:
                return False
            df_new = pd.concat([df_new, ichi], axis=1)
            # Reverse again to get the most recent date on top
            df_new = df_new[::-1]
            df_new = df_new.head(1)
            df_new["cloud_green"] = df_new["ISA_9"].iloc[0] > df_new["ISB_26"].iloc[0]
            df_new["cloud_red"] = df_new["ISB_26"].iloc[0] > df_new["ISA_9"].iloc[0]
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        aboveCloudTop = False
        # baseline > cloud top (cloud is bound by span a and span b) and close is > cloud top
        if df_new["cloud_green"].iloc[0]:
            aboveCloudTop = (
                df_new["IKS_26"].iloc[0] > df_new["ISA_9"].iloc[0]
                and recent["Close"].iloc[0] > df_new["ISA_9"].iloc[0]
            )
        elif df_new["cloud_red"].iloc[0]:
            aboveCloudTop = (
                df_new["IKS_26"].iloc[0] > df_new["ISB_26"].iloc[0]
                and recent["Close"].iloc[0] > df_new["ISB_26"].iloc[0]
            )

        # Latest Ichimoku baseline is < latest Ichimoku conversion line
        if aboveCloudTop and df_new["IKS_26"].iloc[0] < df_new["ITS_9"].iloc[0]:
            # StochRSI crossed 20 and RSI > 50
            if fk > 20 and recent["RSI"].iloc[0] > 50:
                # condition of crossing the StochRSI main signal line from bottom to top
                if (
                    data["FASTD"].iloc[100] < data["FASTK"].iloc[100]
                    and data["FASTD"].iloc[101] > data["FASTK"].iloc[101]
                ):
                    # close > 50 period SMA/EMA and 200 period SMA/EMA
                    if (
                        recent["SSMA"].iloc[0] > recent["SMA"].iloc[0]
                        and recent["Close"].iloc[0] > recent["SSMA"].iloc[0]
                        and recent["Close"].iloc[0] > recent["LMA"].iloc[0]
                    ):
                        screenDict["MA-Signal"] = (
                            colorText.BOLD + colorText.GREEN + "Bullish" + colorText.END
                        )
                        saveDict["MA-Signal"] = "Bullish"
                        return True
        return False

    # Validate VPC
    def validateVCP(
        self, data, screenDict, saveDict, stockName=None, window=3, percentageFromTop=3
    ):
        try:
            percentageFromTop /= 100
            data.reset_index(inplace=True)
            data.rename(columns={"index": "Date"}, inplace=True)
            data["tops"] = (
                data["High"]
                .iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["High"]), np.greater_equal, order=window
                        )[0]
                    )
                ]
                .head(4)
            )
            data["bots"] = (
                data["Low"]
                .iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["Low"]), np.less_equal, order=window
                        )[0]
                    )
                ]
                .head(4)
            )
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            tops = data[data.tops > 0]
            # bots = data[data.bots > 0]
            highestTop = round(tops.describe()["High"]["max"], 1)
            filteredTops = tops[
                tops.tops > (highestTop - (highestTop * percentageFromTop))
            ]
            # print(tops)
            # print(filteredTops)
            # print(tops.sort_values(by=['tops'], ascending=False))
            # print(tops.describe())
            # print(f"Till {highestTop-(highestTop*percentageFromTop)}")
            if filteredTops.equals(tops):  # Tops are in the range
                lowPoints = []
                for i in range(len(tops) - 1):
                    endDate = tops.iloc[i]["Date"]
                    startDate = tops.iloc[i + 1]["Date"]
                    lowPoints.append(
                        data[
                            (data.Date >= startDate) & (data.Date <= endDate)
                        ].describe()["Low"]["min"]
                    )
                lowPointsOrg = lowPoints
                lowPoints.sort(reverse=True)
                lowPointsSorted = lowPoints
                ltp = data.head(1)["Close"].iloc[0]
                if (
                    lowPointsOrg == lowPointsSorted
                    and ltp < highestTop
                    and ltp > lowPoints[0]
                ):
                    screenDict["Pattern"] = (
                        colorText.BOLD
                        + colorText.GREEN
                        + f"VCP (BO: {highestTop})"
                        + colorText.END
                    )
                    saveDict["Pattern"] = f"VCP (BO: {highestTop})"
                    return True
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
        return False

    # Validate if volume of last day is higher than avg
    def validateVolume(self, data, screenDict, saveDict, volumeRatio=2.5):
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        if recent["VolMA"].iloc[0] == 0:  # Handles Divide by 0 warning
            saveDict["Volume"] = 0  # "Unknown"
            screenDict[
                "Volume"
            ] = 0  # colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
            return True
        ratio = round(recent["Volume"].iloc[0] / recent["VolMA"].iloc[0], 2)
        saveDict["Volume"] = ratio  # str(ratio)+"x"
        if (
            ratio >= volumeRatio
            and ratio != np.nan
            and (not math.isinf(ratio))
            and (ratio != 20)
        ):
            screenDict[
                "Volume"
            ] = ratio  # colorText.BOLD + colorText.GREEN + str(ratio) + "x" + colorText.END
            return True
        screenDict[
            "Volume"
        ] = ratio  # colorText.BOLD + colorText.FAIL + str(ratio) + "x" + colorText.END
        return False

    # Find if stock is validating volume spread analysis
    def validateVolumeSpreadAnalysis(self, data, screenDict, saveDict):
        try:
            data = data.head(2)
            try:
                # Check for previous RED candles
                # Current candle = 0th, Previous Candle = 1st for following logic
                if data.iloc[1]["Open"] >= data.iloc[1]["Close"]:
                    spread1 = abs(data.iloc[1]["Open"] - data.iloc[1]["Close"])
                    spread0 = abs(data.iloc[0]["Open"] - data.iloc[0]["Close"])
                    lower_wick_spread0 = (
                        max(data.iloc[0]["Open"], data.iloc[0]["Close"])
                        - data.iloc[0]["Low"]
                    )
                    vol1 = data.iloc[1]["Volume"]
                    vol0 = data.iloc[0]["Volume"]
                    if (
                        spread0 > spread1
                        and vol0 < vol1
                        and data.iloc[0]["Volume"] < data.iloc[0]["VolMA"]
                        and data.iloc[0]["Close"] <= data.iloc[1]["Open"]
                        and spread0 < lower_wick_spread0
                        and data.iloc[0]["Volume"] <= int(data.iloc[1]["Volume"] * 0.75)
                    ):
                        screenDict["Pattern"] = (
                            colorText.BOLD
                            + colorText.GREEN
                            + "Supply Drought"
                            + colorText.END
                        )
                        saveDict["Pattern"] = "Supply Drought"
                        return True
                    if (
                        spread0 < spread1
                        and vol0 > vol1
                        and data.iloc[0]["Volume"] > data.iloc[0]["VolMA"]
                        and data.iloc[0]["Close"] <= data.iloc[1]["Open"]
                    ):
                        screenDict["Pattern"] = (
                            colorText.BOLD
                            + colorText.GREEN
                            + "Demand Rise"
                            + colorText.END
                        )
                        saveDict["Pattern"] = "Demand Rise"
                        return True
            except IndexError as e:
                self.default_logger.debug(e, exc_info=True)
                pass
            return False
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            return False

    """
    # Find out trend for days to lookback
    def validateVCP(data, screenDict, saveDict, daysToLookback=ConfigManager.daysToLookback, stockName=None):
        // De-index date
        data.reset_index(inplace=True)
        data.rename(columns={'index':'Date'}, inplace=True)
        data = data.head(daysToLookback)
        data = data[::-1]
        data = data.set_index(np.arange(len(data)))
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data['tops'] = data['Close'].iloc[list(pktalib.argrelextrema(np.array(data['Close']), np.greater_equal, order=3)[0])]
        data['bots'] = data['Close'].iloc[list(pktalib.argrelextrema(np.array(data['Close']), np.less_equal, order=3)[0])]
        try:
            try:
                top_slope,top_c = np.polyfit(data.index[data.tops > 0], data['tops'][data.tops > 0], 1)
                bot_slope,bot_c = np.polyfit(data.index[data.bots > 0], data['bots'][data.bots > 0], 1)
                topAngle = math.degrees(math.atan(top_slope))
                vcpAngle = math.degrees(math.atan(bot_slope) - math.atan(top_slope))

                # print(math.degrees(math.atan(top_slope)))
                # print(math.degrees(math.atan(bot_slope)))
                # print(vcpAngle)
                # print(topAngle)
                # print(data.max()['bots'])
                # print(data.max()['tops'])
                if (vcpAngle > 20 and vcpAngle < 70) and (topAngle > -10 and topAngle < 10) and (data['bots'].max() <= data['tops'].max()) and (len(data['bots'][data.bots > 0]) > 1):
                    print("---> GOOD VCP %s at %sRs" % (stockName, top_c))
                    import os
                    os.system("echo %s >> vcp_plots\VCP.txt" % stockName)

                    import matplotlib.pyplot as plt                
                    plt.scatter(data.index[data.tops > 0], data['tops'][data.tops > 0], c='g')
                    plt.scatter(data.index[data.bots > 0], data['bots'][data.bots > 0], c='r')
                    plt.plot(data.index, data['Close'])
                    plt.plot(data.index, top_slope*data.index+top_c,'g--')
                    plt.plot(data.index, bot_slope*data.index+bot_c,'r--')
                    if stockName != None:
                        plt.title(stockName)
                    # plt.show()
                    plt.savefig('vcp_plots\%s.png' % stockName)
                    plt.clf()
            except np.RankWarning:
                pass
        except np.linalg.LinAlgError:
            return False
    """
