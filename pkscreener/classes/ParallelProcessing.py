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
 *  Author              :   Pranjal Joshi, Swar Patel
 *  Created             :   18/05/2021
 *  Description         :   Class for managing multiprocessing
"""

import logging
import sys
import warnings

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd

import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.Screener as Screener
import pkscreener.classes.Utility as Utility
from pkscreener import Imports
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import tracelog
from pkscreener.classes.SuppressOutput import SuppressOutput


class StockConsumer:
    def __init__(self):
        self.isTradingTime = Utility.tools.isTradingTime()

    @tracelog
    def screenStocks(
        self,
        executeOption,
        reversalOption,
        maLength,
        daysForLowestVolume,
        minRSI,
        maxRSI,
        respChartPattern,
        insideBarToLookback,
        totalSymbols,
        shouldCache,
        stock,
        newlyListedOnly,
        downloadOnly,
        volumeRatio,
        testbuild=False,
        printCounter=False,
        backtestDuration=0,
        backtestPeriodToLookback=30,
        logLevel=logging.NOTSET,
        monitoring=False,
        hostRef=None,
    ):
        assert (
            hostRef is not None
        ), "hostRef argument must not be None. It should b an instance of PKMultiProcessorClient"
        screeningDictionary, saveDictionary = self.initResultDictionaries()
        fullData = None
        processedData = None
        configManager = hostRef.configManager
        fetcher = hostRef.fetcher
        screener = hostRef.screener
        candlePatterns = hostRef.candlePatterns
        try:
            self.setupLoggers(hostRef, screener, logLevel, stock)
            period = configManager.period
            if volumeRatio <= 0:
                volumeRatio = configManager.volumeRatio
            # Data download adjustment for Newly Listed only feature
            if newlyListedOnly:
                if int(configManager.period[:-1]) > 250:
                    period = "250d"
                else:
                    period = configManager.period
            hostRef.default_logger.info(
                f"For stock:{stock}, stock exists in objectDictionary:{hostRef.objectDictionary.get(stock)}, cacheEnabled:{configManager.cacheEnabled}, isTradingTime:{self.isTradingTime}, downloadOnly:{downloadOnly}"
            )
            if (
                (not shouldCache
                or downloadOnly
                or self.isTradingTime
                or hostRef.objectDictionary.get(stock) is None)
            ):
                data = fetcher.fetchStockData(
                    stock,
                    period,
                    configManager.duration,
                    hostRef.proxyServer,
                    hostRef.processingResultsCounter,
                    hostRef.processingCounter,
                    totalSymbols,
                )
                hostRef.default_logger.info(f"Fetcher fetched stock data:\n{data}")
                if (
                    (shouldCache
                    and not self.isTradingTime
                    and (hostRef.objectDictionary.get(stock) is None))
                    or downloadOnly
                ):
                    hostRef.objectDictionary[stock] = data.to_dict("split")
                    hostRef.default_logger.info(
                        f"Stock data saved:\n{hostRef.objectDictionary[stock]}"
                    )
                    if downloadOnly:
                        raise Screener.DownloadDataOnly
            else:
                if printCounter:
                    try:
                        print(
                            colorText.BOLD
                            + colorText.GREEN
                            + (
                                "[%d%%] Screened %d, Found %d. Fetching data & Analyzing %s..."
                                % (
                                    int(
                                        (hostRef.processingCounter.value / totalSymbols)
                                        * 100
                                    ),
                                    hostRef.processingCounter.value,
                                    hostRef.processingResultsCounter.value,
                                    stock,
                                )
                            )
                            + colorText.END,
                            end="",
                        )
                        print(
                            colorText.BOLD
                            + colorText.GREEN
                            + "=> Done!"
                            + colorText.END,
                            end="\r",
                            flush=True,
                        )
                    except ZeroDivisionError as e:
                        hostRef.default_logger.debug(e, exc_info=True)
                        pass
                    sys.stdout.write("\r\033[K")
                data = hostRef.objectDictionary.get(stock)
                data = pd.DataFrame(
                    data["data"], columns=data["columns"], index=data["index"]
                )
            if len(data) == 0 or len(data) <= backtestDuration:
                return None
            hostRef.default_logger.info(f"Will pre-process data:\n{data.tail(10)}")
            if backtestDuration == 0:
                fullData, processedData = screener.preprocessData(
                    data, daysToLookback=configManager.daysToLookback
                )
            else:
                if data is None or fullData is None or processedData is None:
                    # We want to have the nth day treated as today when pre-processing where n = backtestDuration row from the bottom
                    inputData = data.head(len(data) - backtestDuration + 1)
                    # This will have all the rows in future from the date under consideration 
                    # at the bottom of fullData (or at the top of inputData)
                    data = data.tail(backtestDuration).head(backtestPeriodToLookback+1)
                    fullData, processedData = screener.preprocessData(
                        inputData, daysToLookback=configManager.daysToLookback
                    )
            hostRef.default_logger.info(
                f"Finished pre-processing. processedData:\n{data}\nfullData:{fullData}\n"
            )
            if newlyListedOnly:
                if not screener.validateNewlyListed(fullData, period):
                    raise Screener.NotNewlyListed

            with hostRef.processingCounter.get_lock():
                hostRef.processingCounter.value += 1
                hostRef.default_logger.info(
                    f"Processing {stock} in {hostRef.processingCounter.value}th counter"
                )
            if not processedData.empty:
                screeningDictionary["Stock"] = (
                    colorText.BOLD
                    + colorText.BLUE
                    + (stock if monitoring else f"\x1B]8;;https://in.tradingview.com/chart?symbol=NSE%3A{stock}\x1B\\{stock}\x1B]8;;\x1B\\")
                    + colorText.END
                )
                saveDictionary["Stock"] = stock
                isLtpValid, verifyStageTwo = screener.validateLTP(
                    fullData,
                    screeningDictionary,
                    saveDictionary,
                    minLTP=configManager.minLTP,
                    maxLTP=configManager.maxLTP,
                )
                consolidationValue = screener.validateConsolidation(
                    processedData,
                    screeningDictionary,
                    saveDictionary,
                    percentage=configManager.consolidationPercentage,
                )
                isMaReversal = screener.validateMovingAverages(
                    processedData, screeningDictionary, saveDictionary, maRange=1.25
                )
                if executeOption == 11:
                    isShortTermBullish = screener.validateShortTermBullish(
                        fullData, screeningDictionary, saveDictionary
                    )
                if executeOption == 12:
                    is15MinutePriceVolumeBreakout = (
                        screener.validate15MinutePriceVolumeBreakout(fullData)
                    )
                if executeOption == 13:
                    isBullishIntradayRSIMACD = screener.findBullishIntradayRSIMACD(
                        fullData
                    )
                if executeOption == 14:
                    isNR4Day = screener.findNR4Day(fullData)
                if executeOption == 15:
                    is52WeekLowBreakout = screener.find52WeekLowBreakout(fullData)
                if executeOption == 16:
                    is10DaysLowBreakout = screener.find10DaysLowBreakout(fullData)
                if executeOption == 17:
                    is52WeekHighBreakout = screener.find52WeekHighBreakout(fullData)
                if executeOption == 18:
                    isAroonCrossover = screener.findAroonBullishCrossover(fullData)
                if executeOption == 19:
                    macdHistBelow0 = screener.validateMACDHistogramBelow0(fullData)
                if executeOption == 20:
                    bullishForTomorrow = screener.validateBullishForTomorrow(fullData)
                isVolumeHigh = screener.validateVolume(
                    processedData,
                    screeningDictionary,
                    saveDictionary,
                    volumeRatio=volumeRatio,
                )
                isBreaking = screener.findBreakout(
                    processedData,
                    screeningDictionary,
                    saveDictionary,
                    daysToLookback=configManager.daysToLookback,
                )
                if executeOption == 4:
                    isLowestVolume = screener.validateLowestVolume(
                        processedData, daysForLowestVolume
                    )
                else:
                    isLowestVolume = False
                isValidRsi = screener.validateRSI(
                    processedData, screeningDictionary, saveDictionary, minRSI, maxRSI
                )
                try:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        currentTrend = screener.findTrend(
                            processedData,
                            screeningDictionary,
                            saveDictionary,
                            daysToLookback=configManager.daysToLookback,
                            stockName=stock,
                        )
                except np.RankWarning as e:
                    hostRef.default_logger.debug(e, exc_info=True)
                    screeningDictionary["Trend"] = "Unknown"
                    saveDictionary["Trend"] = "Unknown"
                isValidCci = screener.validateCCI(
                    processedData, screeningDictionary, saveDictionary, minRSI, maxRSI
                )
                isCandlePattern = False
                try:
                    # Only 'doji' and 'inside' is internally implemented by pandas_ta.
                    # Otherwise, for the rest of the candle patterns, they also need
                    # TA-Lib. So if TA-Lib is not available, it will throw exception
                    # We can live with no-patterns if user has not installed ta-lib
                    # yet. If ta-lib is available, PKTalib will load it automatically.
                    isCandlePattern = candlePatterns.findPattern(
                        processedData, screeningDictionary, saveDictionary
                    )
                except Exception as e:
                    hostRef.default_logger.debug(e, exc_info=True)
                    screeningDictionary["Pattern"] = ""
                    saveDictionary["Pattern"] = ""
                isConfluence = False
                isInsideBar = False
                isIpoBase = False
                if newlyListedOnly:
                    isIpoBase = screener.validateIpoBase(
                        stock, fullData, screeningDictionary, saveDictionary
                    )
                if respChartPattern == 3 and executeOption == 7:
                    isConfluence = screener.validateConfluence(
                        stock,
                        processedData,
                        screeningDictionary,
                        saveDictionary,
                        percentage=insideBarToLookback,
                    )
                else:
                    isInsideBar = screener.validateInsideBar(
                        processedData,
                        screeningDictionary,
                        saveDictionary,
                        chartPattern=respChartPattern,
                        daysToLookback=insideBarToLookback,
                    )

                with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                    if (
                        maLength is not None
                        and executeOption == 6
                        and reversalOption == 6
                    ):
                        isNR = screener.validateNarrowRange(
                            processedData,
                            screeningDictionary,
                            saveDictionary,
                            nr=maLength,
                        )
                    else:
                        isNR = screener.validateNarrowRange(
                            processedData, screeningDictionary, saveDictionary
                        )

                isMomentum = screener.validateMomentum(
                    processedData, screeningDictionary, saveDictionary
                )
                if executeOption == 10:
                    isPriceRisingByAtLeast2Percent = (
                        screener.validatePriceRisingByAtLeast2Percent(
                            processedData, screeningDictionary, saveDictionary
                        )
                    )

                isVSA = False
                if not (executeOption == 7 and respChartPattern < 3):
                    isVSA = screener.validateVolumeSpreadAnalysis(
                        processedData, screeningDictionary, saveDictionary
                    )
                if maLength is not None and executeOption == 6 and reversalOption == 4:
                    isMaSupport = screener.findReversalMA(
                        fullData, screeningDictionary, saveDictionary, maLength
                    )

                isVCP = False
                if respChartPattern == 4:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        isVCP = screener.validateVCP(
                            fullData, screeningDictionary, saveDictionary
                        )

                isBuyingTrendline = False
                if executeOption == 7 and respChartPattern == 5:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        if Imports["scipy"]:
                            isBuyingTrendline = screener.findTrendlines(
                                fullData, screeningDictionary, saveDictionary
                            )

                with hostRef.processingResultsCounter.get_lock():
                    hostRef.default_logger.info(
                        f"Processing results for {stock} in {hostRef.processingResultsCounter.value}th results counter"
                    )
                    if executeOption == 0:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if (
                        (executeOption == 1 or executeOption == 2)
                        and isBreaking
                        and isVolumeHigh
                        and isLtpValid
                    ):
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if (
                        (executeOption == 1 or executeOption == 3)
                        and (
                            consolidationValue <= configManager.consolidationPercentage
                            and consolidationValue != 0
                        )
                        and isLtpValid
                    ):
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 4 and isLtpValid and isLowestVolume:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 5 and isLtpValid and isValidRsi:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 6 and isLtpValid:
                        if reversalOption == 1:
                            if (
                                saveDictionary["Pattern"]
                                in CandlePatterns.reversalPatternsBullish
                                or isMaReversal > 0
                            ):
                                hostRef.processingResultsCounter.value += 1
                                return (
                                    screeningDictionary,
                                    saveDictionary,
                                    data,
                                    stock,
                                    backtestDuration,
                                )
                        elif reversalOption == 2:
                            if (
                                saveDictionary["Pattern"]
                                in CandlePatterns.reversalPatternsBearish
                                or isMaReversal < 0
                            ):
                                hostRef.processingResultsCounter.value += 1
                                return (
                                    screeningDictionary,
                                    saveDictionary,
                                    data,
                                    stock,
                                    backtestDuration,
                                )
                        elif reversalOption == 3 and isMomentum:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        elif reversalOption == 4 and isMaSupport:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        elif (
                            reversalOption == 5
                            and isVSA
                            and saveDictionary["Pattern"]
                            in CandlePatterns.reversalPatternsBullish
                        ):
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        elif reversalOption == 6 and isNR:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                    if executeOption == 7 and isLtpValid:
                        if respChartPattern < 3 and isInsideBar:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        if isConfluence:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        if isIpoBase and newlyListedOnly and not respChartPattern < 3:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        if isVCP:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                        if isBuyingTrendline:
                            hostRef.processingResultsCounter.value += 1
                            return (
                                screeningDictionary,
                                saveDictionary,
                                data,
                                stock,
                                backtestDuration,
                            )
                    if executeOption == 8 and isLtpValid and isValidCci:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 9 and isVolumeHigh:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 10 and isPriceRisingByAtLeast2Percent:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 11 and isShortTermBullish:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 12 and is15MinutePriceVolumeBreakout:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 13 and isBullishIntradayRSIMACD:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if executeOption == 14 and isNR4Day:
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
                    if (
                        (executeOption == 15 and is52WeekLowBreakout) or 
                        (executeOption == 16 and is10DaysLowBreakout) or 
                        (executeOption == 17 and is52WeekHighBreakout) or 
                        (executeOption == 18 and isLtpValid and isAroonCrossover) or
                        (executeOption == 19 and macdHistBelow0) or
                        (executeOption == 20 and bullishForTomorrow)
                    ):
                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )

        except KeyboardInterrupt:
            # Capturing Ctr+C Here isn't a great idea
            pass
        except Fetcher.StockDataEmptyException as e:
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except Screener.NotNewlyListed as e:
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except Screener.DownloadDataOnly as e:
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except KeyError as e:
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except Exception as e:
            hostRef.default_logger.debug(e, exc_info=True)
            if testbuild or printCounter:
                print(e)
                print(
                    colorText.FAIL
                    + (
                        "\n[+] Exception Occured while Screening %s! Skipping this stock.."
                        % stock
                    )
                    + colorText.END
                )
        return None

    def setupLoggers(self, hostRef, screener, logLevel, stock):
        # Set the loglevels for both the caller and screener
        # Also add handlers that are specific to this sub-process which
        # will co ntinue with the screening. Each sub-process would have
        # its own logger but going into the same file/console > to that
        # of the parent logger.
        hostRef.default_logger.level = logLevel
        screener.default_logger.level = logLevel
        hostRef.default_logger.addHandlers(log_file_path=None, levelname=logLevel)
        screener.default_logger.addHandlers(log_file_path=None, levelname=logLevel)
        hostRef.default_logger.info(
            f"Beginning the stock screening for stock:{stock}"
        )

    def initResultDictionaries(self):
        screenResults = pd.DataFrame(
            columns=[
                "Stock",
                "Consol.",
                "Breakout",
                "MA-Signal",
                "Volume",
                "LTP",
                "%Chng",
                "RSI",
                "Trend",
                "Pattern",
                "CCI",
            ]
        )
        screeningDictionary = {
            "Stock": "",
            "Consol.": "",
            "Breakout": "",
            "MA-Signal": "",
            "Volume": "",
            "LTP": 0,
            "%Chng": 0,
            "RSI": 0,
            "Trend": "",
            "Pattern": "",
            "CCI": 0,
        }
        saveDictionary = {
            "Stock": "",
            "Consol.": "",
            "Breakout": "",
            "MA-Signal": "",
            "Volume": "",
            "LTP": 0,
            "%Chng": 0,
            "RSI": 0,
            "Trend": "",
            "Pattern": "",
            "CCI": 0,
        }
        
        return screeningDictionary,saveDictionary
