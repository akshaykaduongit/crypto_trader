from Constants import Constants
import time
import json
from datetime import datetime
from Binance import BinacePublic
import configparser
import logging
import os

class BinanceDownloadManager:
    def __init__(self,config_path):
        # load config file
        with open(config_path) as config_file:
            self.dict_config = json.load(config_file)

    def downloadBinaceExchangeInfo(self):
        download_path = self.dict_config["download_paths"]["exchange_info"]
        binance = BinacePublic()
        data = binance.gectExchangeInformation()

        #Updae json file
        with open(download_path, 'w') as outfile:
            json.dump(data, outfile, indent=4)


        data_symbols = {}
        for dict_s in data["symbols"]:
            key = dict_s["symbol"]
            data_symbols[key]=dict_s

        with open(self.dict_config["download_paths"]["symbols_info"], 'w') as outfile:
            json.dump(data_symbols, outfile, indent=4)

    def downloadKlineCandles(self, interval):
        download_path = self.dict_config["download_paths"]["kline_candles"]
        exchange_info_path = self.dict_config["download_paths"]["exchange_info"]
        dict_active_quote_assets = self.dict_config["active_quote_assets"]
        binance = BinacePublic()

        #Get Coin List

        with open(exchange_info_path) as config_file:
            dict_exchange = json.load(config_file)

        dict_root = {}
        # Loop through coin list
        for s in dict_exchange["symbols"]:
            quote_asset = s["quoteAsset"]
            base_asset = s["baseAsset"]
            pair = s["symbol"]
            status = s["status"]

            # skip if quote_asset is to be downloaded
            if quote_asset not in dict_active_quote_assets.keys():
                continue

            # Skip coin if status is not TRADING
            if status != "TRADING":
                continue

            if quote_asset not in dict_root.keys():
                dict_quote = {}
            else:
                dict_quote = dict_root[quote_asset]

            dict_base = binance.getkLineCandlesRaw(pair,interval,None, None, 50)
            dict_quote[base_asset] = dict_base

            dict_root[quote_asset] = dict_quote
            dict_root["update_time"] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)

        #Save candles
        download_path = download_path.format(interval = interval)

        with open(download_path, 'w') as outfile:
            json.dump(dict_root, outfile, indent=4)

#Code starts here
if __name__ == "__main__":
    manager = BinanceDownloadManager(os.path.join("config","config_binance_download.json"))
    manager.downloadBinaceExchangeInfo()
    print("Downloaded exchange info")
    start_time = datetime.now()
    #manager.downloadKlineCandles("1d")
    #print("Downloaded candlesticks for 1d")
    #end_time = datetime.now()
    #process_time = (end_time-start_time).total_seconds()
#    print("Process completed in {} seconds".format(process_time))