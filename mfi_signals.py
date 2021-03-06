from Constants import Constants
import time
import json
from datetime import datetime
from Binance import BinacePublic
from TechnicalAnalysis import OHLC
from TechnicalAnalysis import Indicators
from TechnicalAnalysis import MFISignal
import configparser
from CoinGecko import CoinGecko
from Utilities import Timer
import os


def updateMFISignals():
    # load config file
    # with open(".\\config\\config_mfi_signals.json") as config_file:
    #    dict_pairs = json.load(config_file)
    t = Timer()
    t.start()
    # load config file
    with open(os.path.join("Database","coin_list.json")) as config_file:
        dict_pairs = json.load(config_file)

    dictSignals = {}
    dict_alerts = {}
    b = BinacePublic()
    intervals = ["30m", "1h", "4h", "12h", "1d", "1w"]
    dict_intervals = {"30m": 60, "1h": 900, "4h": 3600, "12h": 7200, "1d": 14400}
    # EUR
    print(dict_pairs)
    dict_quote_mfi = {}
    cg = CoinGecko()
    dict_coin_list = cg.getCoinsMarketCapRankings("EUR")
    print(dict_coin_list)
    dict_last_upd_time = {}

    for quote_symbol, lst_base_symbols in dict_pairs["pair_list"].items():
        # Download for only 3 quote symbols
        if quote_symbol != 'EUR' and quote_symbol != 'BTC' and quote_symbol != 'BNB':
            continue
        # lst_base_symbols = val
        dict_base_mfi = {}
        for base_symbol in lst_base_symbols:

            if base_symbol in dict_coin_list.keys():

                if int(dict_coin_list[base_symbol]) < 2000:
                    pair = base_symbol + quote_symbol
                    dictInt = {}
                    for i in intervals:

                        lst_candles = b.getKlineCandles(pair, i, None, None, 25)
                        if len(lst_candles) < 25:
                            dict_indicators = {}
                            dict_indicators["mfi"] = 200.0
                            dict_indicators["standad_deviation"] = -5
                            dictInt["interval_" + i] = dict_indicators
                            continue

                        # Convert to list of standard OHLC
                        lstOHLC = []
                        for candle in lst_candles:
                            ohlc = candle.ohlc
                            lstOHLC.append(ohlc)

                        # Get MFI signal
                        tc = Indicators()
                        lstOHLC = tc.getMFI(lstOHLC, 14)
                        lstOHLC.reverse()
                        now = datetime.now()
                        mfi = lstOHLC[0].mfi

                        # Standard deviation
                        lstOHLC = []
                        for candle in lst_candles:
                            ohlc = candle.ohlc
                            lstOHLC.append(ohlc)

                        # Get MFI signal
                        tc = Indicators()
                        lstOHLC = tc.getMFI(lstOHLC, 20)
                        lstOHLC.reverse()
                        now = datetime.now()
                        stdev = lstOHLC[0].stdev
                        mean = lstOHLC[0].mean
                        close = lstOHLC[0].close

                        if stdev == 0:
                            s = 0
                        else:
                            s = (mean - close) / stdev

                        dict_indicators = {}
                        dict_indicators["mfi"] = round(mfi, 2)
                        dict_indicators["standad_deviation"] = round(s, 2)

                        dictInt["interval_" + i] = dict_indicators

                        # Add alerts
                        if mfi < 20.0:
                            if pair not in dict_alerts.keys():
                                dict_pair = {}
                            else:
                                dict_pair = dict_alerts[pair]
                            dict_pair["{}_mfi".format(i)] = mfi
                            dict_alerts[pair] = dict_pair

                        if s > 2.25:
                            if pair not in dict_alerts.keys():
                                dict_pair = {}
                            else:
                                dict_pair = dict_alerts[pair]
                            dict_pair["{}_stdev".format(i)] = s
                            dict_alerts[pair] = dict_pair

                    if base_symbol in dict_coin_list.keys():
                        dictInt["market_cap_rank"] = dict_coin_list[base_symbol]

                    dict_base_mfi[base_symbol] = dictInt

        dict_quote_mfi[quote_symbol] = dict_base_mfi
    dictSignals["mfi_values"] = dict_quote_mfi
    dictSignals["update_time"] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
    dictSignals["alerts"] = dict_alerts

    with open("./Database/mfi_signals.json", 'w') as outfile:
        json.dump(dictSignals, outfile, indent=4)
    print("Updated mfi_signals.json file")
    t.end()
    print("pricess tool {} seconds".format(t.getTimeInSeconds()))


# Code start here
while (1 != 2):
    updateMFISignals()
    time.sleep(60 * 20)