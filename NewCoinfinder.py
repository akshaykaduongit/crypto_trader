from Constants import Constants
import time
import json
from datetime import datetime
from Binance import BinacePublic
import configparser
from CoinGecko import CoinGecko
import os


def checkForNewCoin():
    b= BinacePublic()

    symbols = b.getCurrentCoinList()

    dict_current_base_assets = {}
    dict_new_base_Assets = {}
    dict_old_base_assets = {}
    dict_tmp = {}

    # load old coin list
    with open(os.path.join("Database","coin_list.json")) as config_file:
        dict_tmp = json.load(config_file)
    dict_old_base_assets = dict_tmp["base_asset_list"]

    # Load current base asset
    for s in symbols:
        b = s["baseAsset"]
        dict_current_base_assets[b] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)

    # check for new coin
    for s in dict_current_base_assets.keys():
        if s not in dict_old_base_assets:
            dict_new_base_Assets[s] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)

    # Update coin list file
    dict_current = {}
    dict_current["update_time"]= datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
    dict_current["base_asset_list"] = dict_current_base_assets

    # Save coin list to json file
    with open("./Database/coin_list.json", 'w') as outfile:
        json.dump(dict_current, outfile, indent=4)

    return dict_new_base_Assets


new_coins = {}
new_coins = checkForNewCoin()
print(new_coins)