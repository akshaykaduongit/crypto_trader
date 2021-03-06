from Constants import Constants
import time
import json
from datetime import datetime
from Binance import BinacePublic
import configparser
from CoinGecko import CoinGecko


def updatePairList():
    b = BinacePublic()

    symbols = b.getCurrentCoinList()
    dict_pair_list = {}

    for s in symbols:
        quote_asset = s["quoteAsset"]
        base_Asset = s["baseAsset"]
        if quote_asset in dict_pair_list.keys():
            lst_coin = dict_pair_list[quote_asset]
        else:
            lst_coin = []

        lst_coin.append(base_Asset)
        dict_pair_list[quote_asset] = lst_coin

    # Update coin list file
    dict_current = {}
    dict_current["update_time"] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
    dict_current["pair_list"] = dict_pair_list

    # Save coin list to json file
    file_path = "./Database/coin_pair_list.json"
    with open(file_path, 'w') as outfile:
        json.dump(dict_current, outfile, indent=4)

    print("File saved to = {}", format(file_path))


# Code starts here
updatePairList()