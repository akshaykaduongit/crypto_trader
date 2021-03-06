import logging
import requests
from TechnicalAnalysis import OHLC
from TechnicalAnalysis import Indicators
from TechnicalAnalysis import MFISignal
from datetime import datetime
import json


class CoinGecko:
    def __init__(self):
        self.url = "https://api.coingecko.com/api/v3/"


    def getCoinsMarketCapRankings(self,quote_asset):
        #This function will get data of all coins with thwir market capitalisation
        endpoint = "coins/markets"
        # vs_currency=EUR&order=market_cap_desc&per_page=100&page=1&sparkline=false
        payload = {'vs_currency': quote_asset, 'order': 'market_cap_desc', 'per_page': 250, 'page': 1, 'sparkline': 'false'}

        dict_coin_list = {} # key= symbol , value = Market cap order
        url = self.url+endpoint
        r = requests.get(url, allow_redirects=True, params=payload)
        if r.status_code == 200:
            logging.debug("Status code:" + str(r.status_code))
            data = r.json()

            for i, d in enumerate(data):
                symbol = d["symbol"].upper()
                rank = d["market_cap_rank"]
                dict_coin_list[symbol] = rank


        return dict_coin_list
