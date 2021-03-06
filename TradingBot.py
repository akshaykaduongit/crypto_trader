import configparser
from TechnicalAnalysis import OHLC
from TechnicalAnalysis import Indicators
from TechnicalAnalysis import MFISignal
from datetime import datetime
from Portfolio import Transaction
import time
from Binance import BinacePublic, BinancePrivate
import pathlib
import json
import logging
import os
import threading
from plyer import notification
#from MessageQueue import MQManager, MQExchange, MQProducer
from Constants import Constants

BOT_TYPE_MFI = "MFI"
BOT_TYPE_STDEV = "STDEV"


class decision_logEntry:
    def __init__(self, current_price, decision, msg):
        self.decision_time = datetime.utcnow()
        self.current_price = current_price
        self.decision = decision
        self.msg = msg


class TradingBot(threading.Thread):

    def __init__(self, dict):
        threading.Thread.__init__(self)
        logging.debug("inside TradingBot>Constructor")
        self.loadFromBotConfig(dict)
        self.previous_mfi = None
        self.dict_transaction_log = {}
        self.decision_log = []
        self.loadFromBotConfig(dict)
        #self.loadFromDictionary(dict)
        self.last_buy_open_time = None
        self.save()

    def loadFromBotConfig(self,dict):
        self.type = dict["type"]
        self.base_symbol = dict["base_symbol"]
        self.quote_symbol = dict["quote_symbol"]
        self.interval = dict["interval"]
        self.initial_amount = float(dict["initial_amount"])
        self.stop_loss = float(dict["stop_loss"])
        self.take_profit = float(dict["take_profit"])
        self.trailing_Stop_loss = float(dict["trailing_stop_loss"])
        self.id = "{}_{}{}_{}".format(self.type, self.base_symbol, self.quote_symbol, self.interval)
        self.pair = self.base_symbol + self.quote_symbol

    def loadFromDictionary(self, dict):
        # Set values from parameters
        #self.type = dict["type"]
        #self.base_symbol = dict["base_symbol"]
        #self.quote_symbol = dict["quote_symbol"]
        
        #self.interval = dict["interval"]
        #self.initial_amount = float(dict["initial_amount"])
        #self.stop_loss = float(dict["stop_loss"])
        #self.take_profit = float(dict["take_profit"])
        #self.trailing_Stop_loss = float(dict["trailing_stop_loss"])
        #self.id = "{}_{}{}_{}".format(self.type, self.base_symbol, self.quote_symbol, self.interval)
        #self.pair = self.base_symbol + self.quote_symbol

        self.base_quantity = None
        self.current_price = None
        self.previous_price = None

        self.current_amount = float(self.initial_amount)
        if "current_amount" in dict.keys():
            self.current_amount = dict["current_amount"]

        if "base_quantity" in dict.keys() and dict["base_quantity"] is not None:
            self.base_quantity = float(dict["base_quantity"])

        if "current_price" in dict.keys() and dict["current_price"] is not None:
            self.current_price = float(dict["current_price"])

        if "previous_price" in dict.keys() and dict["previous_price"] is not None:
            self.previous_price = float(dict["previous_price"])

        # Selling attrubutes
        self.trailing_stop_loss_enabled = None
        self.current_stop_loss_price = None
        self.current_take_profit_price = None
        if "trailing_stop_loss_enabled" in dict.keys() and dict["trailing_stop_loss_enabled"] is not None:
            self.trailing_stop_loss_enabled = bool(dict["trailing_stop_loss_enabled"])

        if "current_stop_loss_price" in dict.keys() and dict["current_stop_loss_price"] is not None:
            self.current_stop_loss_price = float(dict["current_stop_loss_price"])

        if "current_take_profit_price" in dict.keys() and dict["current_take_profit_price"] is not None:
            self.current_take_profit_price = float(dict["current_take_profit_price"])

        # Indicators
        self.current_mfi = None
        self.current_stdev = None
        self.current_mean = None
        self.previous_mfi = None

        if "current_mfi" in dict.keys() and dict["current_mfi"] is not None:
            self.current_mfi = float(dict["current_mfi"])

        if "current_stdev" in dict.keys() and dict["current_stdev"] is not None:
            self.current_stdev = float(dict["current_stdev"])

        if "current_mean" in dict.keys() and dict["current_mean"] is not None:
            self.current_mean = float(dict["current_mean"])

        # Status
        self.is_active = False
        self.status = "SEARCHING"

        if "is_active" in dict.keys() and dict["is_active"] is not None:
            self.is_active = bool(dict["is_active"])

        if "status" in dict.keys() and dict["status"] is not None:
            self.status = dict["status"]

        self.current_transaction = None
        if "current_transaction" in dict.keys():
            trans = Transaction()
            trans.loadFromDictionary(dict["current_transaction"])
            self.current_transaction = trans

        # TODO : Load transaction log
        try:
            if "transaction_log" in dict.keys():
                for k,d in dict["transaction_log"].items():
                    self.dict_transaction_log[k] = d
        except:
            self.logger("error occured while loading transaction log")


        # If no transaction is open then set status to SEARCHING
        if self.current_transaction is None:
            self.status = "SEARCHING"

        b = BinacePublic()
        # self.updatePrice(b.getAveragePrice(self.pair))
        self.updatePrice(b.getLatestPrice(self.pair))

        self.log_file_name = ""
        self.logger = logging.getLogger(self.id)
        self.setLogger()
        self.save_file_path = os.path.join("Database","bots_state",  self.id + ".json")
        self.active_file_path = os.path.join("Database","bots_active" , self.id + ".top")

    def sendHeartBeat(self):

        try:

            msg_dict = {}
            msg_dict["id"] = self.id
            msg_dict["pair"] = self.pair
            msg_dict["interval"] = self.interval
            msg_dict["bot_type"] = self.type
            msg_dict["status"] = self.status
            msg_dict["time"] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
            msg_dict["current_price"] = round(self.current_price, 4)
            msg_dict["current_amount"] = round(self.current_amount, 4)
            indicators_info = {}
            if self.type == "MFI" and self.current_mfi is not None:
                indicators_info["current_mfi"] = round(self.current_mfi, 4)

            if self.type == "STDEV" and self.current_mean is not None:
                indicators_info["current_mean"] = round(self.current_mean, 4)
                indicators_info["current_stdev"] = round(self.current_stdev, 4)
                threshold_price = self.current_mean - 2.25 * self.current_stdev
                indicators_info["threshold_price"] = round(threshold_price, 4)
                indicators_info["threshold_gain"] = round(
                    ((self.current_price - threshold_price) / (self.current_mean - threshold_price)) * 100, 4)

            if indicators_info:
                msg_dict["indicators_info"] = indicators_info

            producer.postMessage("heart_beat", msg_dict)
        except:
            self.logger.exception("Error occured in TradingBot>sendheartBeat()")

    def sendCurrentTransaction(self):
        try:

            if self.current_transaction is not None:
                PATH = "C:\\Users\\171802\\PycharmProjects\\Binance\\venv\\MessageQueue"
                mq = MQManager(PATH)
                exchange = mq.getExchange("Binance")
                producer = exchange.getProducer()
                msg_dict = self.current_transaction.getDictionary()
                producer.postMessage("Transactions", msg_dict)

        except:
            self.logger.exception("Error occured in TradingBot>sendCurrentTransaction()")

    def loadFromJsonFile(self):
        try:
            # Leave if file does not exist
            if not os.path.isfile(self.save_file_path):
                self.logger.info("Save stat file not found")
                return

            self.logger.info("Save stat file found, loading information from file")
            dict = {}
            with open(self.save_file_path) as config_file:
                dict = json.load(config_file)

            if dict is None:
                return

            self.loadFromDictionary(dict)
            self.logger.info("Information loaded from save state file")
        except:
            self.logger.exception("Error occured in TradigBot>loadFromJsonFile")

    def setLogger(self):
        self.log_file_name = os.path.join("Logs",  self.id + ".txt")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler = logging.FileHandler(self.log_file_name)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        # logging.basicConfig(filename=self.log_file_name,
        #                     level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')

    def stop(self):
        self.is_active = False
        self.save()
        self.deleteActiveFile()

    def run(self):
        try:
            print("Inside TradingBot>run")
            self.createActiveFile()
            # self.publishToDesktop(self.id , "Bot started")
            self.logger.debug("Inside TradingBot>run")
            self.save()
            if self.is_active == False:
                self.logger.info("Bot is inactive")
                return

            while self.is_active == True:
                self.save()

                # Check if active file is present

                # When status is Searching - this function will call checkForBuy at specific interval
                # If MFI is more than 30 then check status every 5 mins to reduce log and unnecessary requests

                if self.type == "MFI" and self.status == "SEARCHING":
                    self.checkForBuy_MFI()
                    self.logger.info(
                        self.id + "Current status:{}, Price:{}, MFI:{}".format(self.status, str(self.current_price),
                                                                               str(self.current_mfi)))
                    time.sleep(120)

                elif self.type == "MFI" and self.status == "BUY_WATCH":
                    self.checkForBuy_MFI()
                    time.sleep(60)

                elif self.type == "STDEV" and self.status == "SEARCHING":

                    self.checkForBuy_STDEV()
                    self.logger.info(
                        self.id + "Current status:{}, Price:{}, Mean:{}, STDEV:{},Lower BB Band:{}".format(self.status,
                                                                                                           str(
                                                                                                               self.current_price),
                                                                                                           str(
                                                                                                               self.current_mean),
                                                                                                           str(
                                                                                                               self.current_stdev),
                                                                                                           str(
                                                                                                               self.current_mean - 2 * self.current_stdev)))
                    time.sleep(180)

                elif self.type == "STDEV" and self.status == "BUY_WATCH":

                    self.checkForBuy_STDEV()
                    self.logger.info(
                        self.id + "Current status:{}, Price:{}, Mean:{}, STDEV:{},Lower BB Band:{}".format(
                            self.status, str(self.current_price),
                            str(self.current_mean), str(self.current_stdev),
                            str(self.current_mean - 2 * self.current_stdev)))
                    time.sleep(30)

                elif self.type == "MA" and self.status == "SEARCHING":
                    self.checkForBuy_MA()
                    time.sleep(30)

                # When status is Open -- this function will call check ForSale at specific interval
                elif self.status == "OPEN":
                    self.checkforSell()

                    # Send to Message Queue
                    #self.sendCurrentTransaction()

                    time.sleep(15)
        except:
            self.logger.exception("Error occured in TradingBot>Run")

    def checkForBuy_MA(self):
        try:
            self.logger.debug("Inside TradingBot>checkForBuy_MA")
            # Fetch candle stick data fron Binance API
            binance = BinacePublic()
            lst_candles = binance.getKlineCandles(self.pair, self.interval, None, None, 25)

            if self.last_buy_open_time is not None and self.last_buy_open_time == lst_candles[-1].openTime:
                self.logger.info("Coin was bought recently hence skipping")
                return

            # Convert to list of standard OHLC
            lstOHLC = []
            for candle in lst_candles:
                ohlc = candle.ohlc
                lstOHLC.append(ohlc)

            lstOHLC2 = lstOHLC.copy()

            # Get MFI signal
            tc = Indicators()
            lstOHLC19 = tc.getMFI(lstOHLC, 19)
            #lstOHLC19.reverse()
            ma19_current = lstOHLC19[-1].mean
            ma19_previous = lstOHLC19[-2].mean

            lstOHLC13 = tc.getMFI(lstOHLC2, 13)
            #lstOHLC13.reverse()
            ma13_current = lstOHLC13[-1].mean
            ma13_previous = lstOHLC13[-2].mean
            # Update current price

            self.updatePrice(lstOHLC13[-1].close)
            if lstOHLC19[0].stdev == 0:
                s = 0
            else:
                s = (ma13_current - lstOHLC13[0].close) / lstOHLC13[0].stdev

            self.logger.info(
                self.id + " Current MA13:" + str(ma13_current) + ",MA19:" + str(ma19_current)+"MA19 price:"+str(lstOHLC19[-1].close))
            if self.status == "SEARCHING":
                # MA 13 cross over MA 19 and value is not beyond upper limit of bollinger band
                if ma13_current > ma19_current and ma13_previous < ma19_previous and s > -1.5:
                    self.buy("MA13 crossed MA19")
                    self.last_buy_open_time = lst_candles[-1].openTime




        except:
            self.logger.exception("Error occured in TradingBot>CheckForBuy_MA")

    def checkForBuy_MFI(self):
        try:
            self.logger.debug("Inside TradingBot>CheckForBuy_MFI")

            # Fetch candle stick data fron Binance API
            binance = BinacePublic()
            lst_candles = binance.getKlineCandles(self.pair, self.interval, None, None, 20)

            # Convert to list of standard OHLC
            lstOHLC = []
            for candle in lst_candles:
                ohlc = candle.ohlc
                lstOHLC.append(ohlc)

            # Get MFI signal
            tc = Indicators()
            lstOHLC = tc.getMFI(lstOHLC, 7)
            lstOHLC.reverse()
            now = datetime.now()

            # Update current and previous MFI prices
            if self.current_mfi is not None:
                self.previous_mfi = self.current_mfi

            self.current_mfi = lstOHLC[0].mfi
            if self.previous_mfi is None:
                self.previous_mfi = lstOHLC[1].mfi

            sig = MFISignal(now, self.previous_mfi, self.current_mfi, lstOHLC[0].close)
            self.logger.info(
                self.id + " Current MFI:" + str(self.current_mfi) + ",Previous MFI" + str(self.previous_mfi))
            self.updatePrice(lstOHLC[0].close)

            if self.status == "SEARCHING" and self.current_mfi < 18:
                self.status = "BUY_WATCH"
                self.logger.info("Status changed to BUY_WATCH, current MFI:{}".format(str(self.current_mfi)))
                return

            if self.status == "BUY_WATCH" and self.previous_mfi == 0.0 and self.current_mfi > 2:
                self.buy("MFI changed from ZERO to positive value")

            # elif self.status == "BUY_WATCH" and sig.signalType == "OVERSOLD-NORMAL":
            elif self.status == "BUY_WATCH" and self.current_mfi > 20.0:
                self.buy("MFI signal:" + sig.signalType)

            elif self.status == "BUY_WATCH" and self.current_mfi > 30.0:
                self.status = "SEARCHING"

        except:
            self.logger.exception("Error occured in TradingBot>CheckForBuy_MFI")

    def checkForBuy_STDEV(self):
        try:
            self.logger.debug("Inside TradingBot>checkForBuy_SDEV")
            # Fetch candle stick data fron Binance API
            binance = BinacePublic()
            lst_candles = binance.getKlineCandles(self.pair, self.interval, None, None, 25)

            # Convert to list of standard OHLC
            lstOHLC = []
            for candle in lst_candles:
                ohlc = candle.ohlc
                lstOHLC.append(ohlc)

            # Get SDEV
            tc = Indicators()
            lstOHLC = tc.getMFI(lstOHLC, 20)
            lstOHLC.reverse()
            now = datetime.now()

            self.updatePrice(lstOHLC[0].close)
            self.current_stdev = lstOHLC[0].stdev
            self.current_mean = lstOHLC[0].mean

            # Log current values
            self.logger.info(
                self.id + " Current status:{}, Price:{}, Mean:{}, STDEV:{},Lower BB Band:{}".format(self.status, str(
                    self.current_price), str(self.current_mean), str(self.current_stdev), str(
                    self.current_mean - 2 * self.current_stdev)))

            if self.status == 'SEARCHING' and self.current_price < self.current_mean - self.current_stdev * 2.5:
                self.status = "BUY_WATCH"
                self.buy_watch_lowest_price = self.current_price
                self.logger.info(
                    "Status changed to BUY_WATCH, current price: {}, Standard Deviation: {}, Mean {}".format(
                        str(self.current_price), str(lstOHLC[0].stdev), str(lstOHLC[0].mean)))
                return

            if self.status == 'SEARCHING' and lstOHLC[0].open - self.current_price > self.current_mean - self.current_stdev * 2.25:
                self.status = "BUY_WATCH"
                self.buy_watch_lowest_price = self.current_price
                self.logger.info(
                    "Status changed to BUY_WATCH, current price: {}, Standard Deviation: {}, Mean {}".format(
                        str(self.current_price), str(lstOHLC[0].stdev), str(lstOHLC[0].mean)))
                return

            if self.status == "BUY_WATCH" and self.current_price < self.buy_watch_lowest_price:
                self.buy_watch_lowest_price = self.current_price
                return

            if self.status == "BUY_WATCH" and self.current_price > self.buy_watch_lowest_price *1.01 :
                self.buy("current price is more than previous price")

            # TODO: when bot is stopped and status = "BUY_WATCH" change status to searching
            # if no open transaction then change status to searching

        except:
            self.logger.exception("Error occured in TradingBot>checkForBuy_SDEV")

    def checkforSell(self):
        try:
            logging.debug("Inside TradingBot>checkforSell")
            if self.status != "OPEN":
                self.addDeicsionLog("ERROR", "No transaction to close")
                return

            # Update current price
            binance = BinacePublic()
            # self.updatePrice(binance.getAveragePrice(self.pair))
            self.updatePrice(binance.getLatestPrice(self.pair))

            # If price falls below stop loss price then sell
            if self.current_price < self.current_stop_loss_price:
                self.addDeicsionLog("SELL", "Current price falls below Stop loss price")
                self.sell("Current price falls below Stop loss price")
                return

            # If price crosses take profit then enable trailing stop loss
            if (
                    self.trailing_stop_loss_enabled is None or self.trailing_stop_loss_enabled == False) and self.current_price > self.current_take_profit_price:
                self.trailing_stop_loss_enabled = True
                self.current_stop_loss_price = self.current_price
                #self.current_stop_loss_price = self.current_price * (100 - self.trailing_Stop_loss) / 100
                self.addDeicsionLog("HOLD",
                                    "Trailing stoploss enabled,take_profit=" + str(self.current_take_profit_price))
                return

            # If Trailing stop loss is enabled then update current stop loss price based on current price
            if self.trailing_stop_loss_enabled == True and self.current_price > self.previous_price:
                tmp_stop_loss_price = self.current_price * (100 - self.trailing_Stop_loss) / 100
                if tmp_stop_loss_price > self.current_stop_loss_price:
                    self.current_stop_loss_price = tmp_stop_loss_price
                    self.addDeicsionLog("HOLD", "Reset stoploss price to " + str(self.current_stop_loss_price))
                return
        except:
            self.logger.exception("Error occured in TradingBot>chekForSell")

    def updatePrice(self, current_price):
        if self.current_price == None:
            self.previous_price = current_price
            self.current_price = current_price
        else:
            self.previous_price = self.current_price
            self.current_price = current_price

    def sell(self, sell_reason):
        try:
            self.logger.debug("Inside TradingBot>Sell")
            self.logger.info("SELL action , current price:" + str(self.current_price))
            self.logger.info("SELL Reason:" + sell_reason)

            # Execute sell order and get actual sell price
            bp = BinancePrivate()
            order_response = bp.order_market_sell(self.pair,self.base_quantity)
            sell_price = order_response["average_price"]

            # Calculate current amount based on current price
            self.base_quantity = None
            self.current_transaction.closeTransaction(sell_price, datetime.now(), sell_reason)
            self.current_amount = self.current_amount + self.current_transaction.final_amount
            self.logger.info(json.dumps(self.current_transaction.getDictionary()))

            # Send to Message Queue
            # self.sendCurrentTransaction()

            # Add current trasaction to log
            self.updateTransactionLog()
            self.logger.info("SELL action, Quantity:{}, Sell Price:{}".format(self.current_transaction.quantity,self.current_transaction.sell_price))
            # Reset parameters
            self.current_transaction = None
            self.current_stop_loss_price = None
            self.current_take_profit_price = None
            self.trailing_stop_loss_enabled = None
            self.status = "SEARCHING"
            #self.publishToDesktop(self.id + " - SELL Action","Reason:{}, Current amount:{}".format(sell_reason, sell_price))

        except:
            self.logger.exception("Error occured in TradingBot>Sell")

    def updateTransactionLog(self):
        key = self.current_transaction.buy_time.strftime(Constants.STANDARD_DATE_FORMAT)
        self.dict_transaction_log[key] = self.current_transaction.getDictionary()

    def buy(self, buy_reason):
        try:
            self.logger.debug("Inside TradingBot>buy")
            # Fetch candle stick data fron Binance API
            binance = BinacePublic()
            self.updatePrice(binance.getLatestPrice(self.pair))

            self.logger.info("BUY action , current price:" + str(self.current_price))
            # Always buy with 80% of current amount to cover fees
            max_Available_for_buy = self.current_amount * 0.8
            self.base_quantity = max_Available_for_buy / self.current_price

            self.logger.info("BUY Action, Quantity: {}".format(self.base_quantity))
            # Send request to buy
            # TODO: Add functionality to actual buy
            bp = BinancePrivate()
            order_response = bp.order_market_buy(self.pair,self.base_quantity)
            buy_price = order_response["average_price"]
            self.base_quantity = order_response["total_quantity"]

            # Get actual price

            # Update actualprice, currentAmpunt and status
            trans_dict = {}
            trans_dict["pair"] = self.pair
            trans_dict["key"] = self.pair + self.interval + datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
            trans_dict["quantity"] = self.base_quantity
            trans_dict["buy_time"] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
            #trans_dict["buy_price"] = self.current_price
            trans_dict["buy_price"] = buy_price
            trans_dict["buy_reason"] = buy_reason
            self.current_transaction = Transaction()
            self.current_transaction.loadFromDictionary(trans_dict)

            self.current_amount = self.current_amount - self.base_quantity * self.current_price - self.current_transaction.buy_fees
            self.current_stop_loss_price = self.current_price * (100 - self.stop_loss) / 100
            self.current_take_profit_price = self.current_price * (100 + self.take_profit) / 100
            self.logger.info("BUY action , actual buy price:{}".format( buy_price))
            self.status = "OPEN"
            #self.publishToDesktop(self.id + " - BUY Action", buy_reason)
        except:
            self.logger.exception("Error occured in TradingBot>buy")

    def addDeicsionLog(self, decision, msg):
        decision = decision_logEntry(self.current_price, decision, msg)
        self.decision_log.append(decision)
        pass

    def save(self):
        try:
            # convert to JSON string
            dict = self.getDictionary()

            with open(self.save_file_path, 'w') as outfile:
                json.dump(dict, outfile, indent=4)

            # self.sendHeartBeat()
        except:
            self.logger.exception("Error occured in TradingBot>save()")

    def getDictionary(self):
        try:
            dict = {}
            dict["update_time"] = datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
            dict["type"] = self.type
            dict["status"] = self.status
            dict["base_symbol"] = self.base_symbol
            dict["quote_symbol"] = self.quote_symbol
            dict["interval"] = self.interval
            dict["is_active"] = self.is_active
            dict["initial_amount"] = self.initial_amount
            dict["current_amount"] = self.current_amount
            dict["base_quantity"] = self.base_quantity
            dict["current_price"] = self.current_price
            dict["previous_price"] = self.previous_price
            dict["current_mfi"] = self.current_mfi
            dict["current_stdev"] = self.current_stdev
            dict["current_mean"] = self.current_mean
            dict["log_file_name"] = self.log_file_name

            dict["stop_loss"] = self.stop_loss
            dict["take_profit"] = self.take_profit
            dict["trailing_stop_loss"] = self.trailing_Stop_loss

            if self.current_stop_loss_price is not None:
                dict["current_stop_loss_price"] = self.current_stop_loss_price
                dict["current_take_profit_price"] = self.current_take_profit_price
                dict["trailing_stop_loss_enabled"] = self.trailing_stop_loss_enabled

            if self.current_transaction is not None:
                dict["current_transaction"] = self.current_transaction.getDictionary()

            if self.dict_transaction_log is not None:
                dict["transaction_log"] = self.dict_transaction_log

            return dict
        except:
            self.logger.exception("Error occured in TradingBot>getDictionary()")

    def publishToDesktop(self, title, msg):
        notification.notify(
            # title of the notification,
            title="{} notification on {}".format(title, datetime.now()),
            # the body of the notification
            message=msg,
            # creating icon for the notification
            # we need to download a icon of ico file format
            # app_icon = "Paomedia-Small-N-Flat-Bell.ico",
            # the notification stays for 50sec
            timeout=50
        )

    def createActiveFile(self):
        f = open(self.active_file_path, "w")
        f.write(self.id)
        f.close()

    def checkActiveFile(self):
        if os.path.exists(self.active_file_path):
            self.is_active = True
        else:
            self.is_active = False

    def deleteActiveFile(self):
        os.remove(self.active_file_path)


if __name__ == "__main__":
    PATH = "/Users/akshaykadu/PycharmProjects/Binance/venv/MessageQueue"
#    mq = MQManager(PATH)
#   exchange = mq.getExchange("Binance")
#    producer = exchange.getProducer()

# TODO : Ability to start and stop Bot
# TODO : Stop bot if loss in 3 consecutive transactions or current amount falls below 80% of initial amount
# TODO : Rotating log file handler
