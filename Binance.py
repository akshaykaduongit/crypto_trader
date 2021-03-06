import logging
import requests
from TechnicalAnalysis import OHLC
from TechnicalAnalysis import Indicators
from TechnicalAnalysis import MFISignal
from datetime import datetime
import json
from binance.client import Client
import os

class BinancePrivate:
    def __init__(self):
        self.api_key = "THMrraVxI5cD8FYtbrJcfged6URzbJRujMH9zkN88mqHc3bQDlAsbuUZAAbxxK2d"
        self.api_secret = "LkVaa9AA1SO3RuoZdcYCiaWCiq90cOeojg4VQOwxt23t6cMC2OCCw5M51uwr6XbU"
        self.client = Client(self.api_key, self.api_secret)
        # load config file
        dict_config = {}
        with open(os.path.join("config","config_binance_download.json")) as config_file:
            dict_config = json.load(config_file)

        symbols_info_path = dict_config["download_paths"]["symbols_info"]
        self.dict_symbols = {}
        with open(symbols_info_path) as config_file:
            self.dict_symbols = json.load(config_file)

    def order_market_buy(self,pair, qty):

        qty = round(qty,self.dict_symbols[pair]["quotePrecision"])
        dict_lot_size = {}
        for flt in self.dict_symbols[pair]["filters"]:
            if flt["filterType"] == "LOT_SIZE":
                dict_lot_size = flt

        lot_step_size = float(dict_lot_size["stepSize"])
        if lot_step_size != 0.0:
            m = qty%lot_step_size
            qty = qty-m

        print("BUY order, symbol={}, quantity = {}".format(pair,qty))

        order = self.client.order_market_buy(    symbol=pair,    quantity=qty)
        q = 0
        pq = 0
        for f in order["fills"]:
            q = q + float(f["qty"])
            pq = pq + float(f["qty"]) * float(f["price"])

        avg_price = pq/q
        order["average_price"] = avg_price
        order["total_quantity"] = q

        return order


    def order_market_sell(self,pair, qty):
        qty = round(qty, self.dict_symbols[pair]["quotePrecision"])
        order = self.client.order_market_sell(    symbol=pair,    quantity=qty)
        q = 0
        pq = 0
        for f in order["fills"]:
            q = q + float(f["qty"])
            pq = pq + float(f["qty"]) * float(f["price"])

        avg_price = pq/q
        order["average_price"] = avg_price
        order["total_quantity"] = q

        return order


class BinacePublic:
    def __init__(self):
        logging.debug("Inside BinancePublic>Constructor")
        self.api_url="https://api.binance.com"

    def getAveragePrice(self,pair):
        logging.debug("Inside BinancePublic>getAveragePrice")
        endpoint = "/api/v3/ticker/price?symbol={symbol}"
        url = self.api_url+endpoint
        url = url.replace("{symbol}",pair)
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 200:
            data = r.json()
            return float(data["price"])
        else:
            return -1

    def getLatestPrice(self,pair):
        data = self.getKlineCandles(pair,"30m",None,None,2)
        return data[-1].ohlc.close

    def getServerTime(self):
        logging.debug("Inside BinancePublic>getServerTime")
        endpoint = "/api/v3/time"
        url = self.api_url + endpoint
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 200:
            data = r.json()
            return float(data["serverTime"])
        else:
            return -1

    def gectExchangeInformation(self):
        logging.debug("Inside BinancePublic>gectExchangeInformation")
        endpoint = "/api/v3/exchangeInfo"
        url = self.api_url + endpoint
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 200:
            data = r.json()
            return data
        else:
            return -1


    def getCurrentCoinList(self):
        info = {}
        info = self.gectExchangeInformation()
        symbols = info["symbols"]
        return symbols

    def getkLineCandlesRaw(self,pair,interval,startTime,endTime,limit):
        endpoint = "/api/v3/klines"
        url = self.api_url + endpoint
        if startTime is None or endTime is None:
            payload = {'symbol': pair, 'interval': interval, 'limit': limit}
        else:
            payload = {'symbol': pair, 'interval': interval, 'startTime': startTime, 'endTime': endTime, 'limit': limit}


        print("Payload:" + str(payload))
        r = requests.get(url, allow_redirects=True, params=payload)
        if r.status_code == 200:
            logging.debug("Status code:" + str(r.status_code))
            data = r.json()

        return data

    def getKlineCandles(self,pair,interval,startTime,endTime,limit):
        #print("Start time:"+str(startTime))
        #print("End time:" + str(endTime))
        logging.debug("Inside BinancePublic>getKlineCandles")
        lstCandles = []
        endpoint = "/api/v3/klines"
        url = self.api_url + endpoint
        if startTime is None or endTime is None:
            payload = {'symbol': pair, 'interval': interval, 'limit': limit}
        else:
            payload = {'symbol': pair, 'interval': interval, 'startTime': startTime, 'endTime': endTime, 'limit': limit}

        print("Payload:"+str(payload))
        r = requests.get(url, allow_redirects=True,params=payload)
        if r.status_code == 200:
            logging.debug("Status code:"+str(r.status_code))
            data = r.json()

            for i,d in enumerate(data):
                #logging.debug("Candle"+str(i))
                candle = BinanceCandleStick()
                candle.openTime = d[0]
                ohlc = OHLC(float(d[1]),float(d[2]),float(d[3]),float(d[4]),float(d[5]))
                candle.ohlc = ohlc
                candle.closeTime = d[6]
                candle.quoteAssetVolume = d[7]
                candle.numberOfTrades = d[8]
                candle.takerBaseAssetBuyVolume = d[9]
                candle.takerQuoteAssetBuyVolume = d[10]
                lstCandles.append(candle)

            return lstCandles
        else:
            return -1

class BinanceCandleStick:
    def __init__(self):
        self.openTime = None
        self.closeTime = None
        self.ohlc = None
        self.quoteAssetVolume = None
        self.numberOfTrades = None
        self.takerBaseAssetBuyVolume = None
        self.takerQuoteAssetBuyVolume = None

    def print(self):
        print("************************************************************")
        print("openTime                 :"+str(self.openTime))
        print("closeTime                :"+str(self.closeTime))
        print("Open                     :"+str(self.ohlc.open))
        print("High                     :"+str(self.ohlc.high))
        print("Low                      :"+str(self.ohlc.low))
        print("Close                    :"+str(self.ohlc.close))
        print("Volume                   :"+str(self.ohlc.volume))
        print("quoteAssetVolume         :"+str(self.quoteAssetVolume))
        print("numberOfTrades           :"+str(self.numberOfTrades))
        print("takerBaseAssetBuyVolume  :"+str(self.takerBaseAssetBuyVolume))
        print("takerQuoteAssetBuyVolume :"+str(self.takerQuoteAssetBuyVolume))

'''
# code starts here
#logging.basicConfig(filename = "Binancelog.txt",level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
b = BinacePublic()
#print(b.getAveragePrice("VETUSD"))
#b.gectExchangeInformation()
lstCandles = b.getKlineCandles('BTCEUR','1h',0,0,16)
logging.debug("Candle count:"+str(len(lstCandles)))

logging.debug("Printng candle data:")
lstOHLC = []
for candle in lstCandles:
    ohlc = candle.ohlc
    lstOHLC.append(ohlc)

tc = Indicators()
# Calculate MFI
lstOHLC = tc.getMFI(lstOHLC,14)
lstOHLC.reverse()
now=datetime.utcnow()
sig = MFISignal(now,lstOHLC[1].mfi,lstOHLC[0].mfi,lstOHLC[0].close)

logging.debug("MFI signal:"+sig.signalType)
print(sig.signalType)
'''
if __name__ == '__main__':
    baseAsset = "XRP"
    quoteAsset = "EUR"
    interval = "1h"
    b = BinacePublic()
    lstCandles = b.getKlineCandles(baseAsset+quoteAsset,interval,0,0,16)
    print(len(lstCandles))

    # Convert to list of standard OHLC
    lstOHLC = []
    for candle in lstCandles:
        candle.print()
        ohlc = candle.ohlc
        lstOHLC.append(ohlc)

    # Get MFI signal
    tc = Indicators()
    lstMFI = tc.getMFI(lstOHLC, 7)
    lstOHLC.reverse()
    now = datetime.utcnow()
    sig = MFISignal(now, lstOHLC[1].mfi, lstOHLC[0].mfi, lstOHLC[0].close)
    lstOHLC[0].print()
    print(lstOHLC[0].mfi)


    #Get current candle data
    latest_Candle = lstCandles[len(lstCandles)-1]
    latest_candlt_open_time = latest_Candle.openTime
    servertime = b.getServerTime()

    lstCandles2 = b.getKlineCandles(baseAsset + quoteAsset, '1m', latest_Candle.closeTime, b.getServerTime(), 500)

    #loop for volume
    vol = 0.0
    count = 0
    for c in lstCandles2:
        open_time = c.openTime
        if open_time > latest_candlt_open_time:
            vol = vol + float(c.ohlc.volume)
            count = count + 1

    print("Volume:"+str(vol)+"Count:"+str(count))

    print("1m cnadle Length ="+str(len(lstCandles2)))
    print("First candle closeTime="+str(lstCandles2[0].closeTime))
    print("Last candle closeTime="+str(lstCandles2[len(lstCandles2)-1].closeTime))
    print(str(datetime.utcnow().timestamp() * 1000))
