import os
import json
import logging
from datetime import datetime
from MessageQueue import MQManager, MQExchange, MQConsumer
import time
from Utilities import Utilities
from Constants import Constants


class DecisionLogEntry:
    def __init__(self, current_price, decision, msg):
        self.decision_time = datetime.utcnow()
        self.current_price = current_price
        self.decision = decision
        self.msg = msg


class Transaction:
    def __init__(self):
        logging.debug("Inside Transaction constructor")
        self.pair = None
        self.key = None
        self.quantity = None
        self.buy_time = None
        self.buy_price = None
        self.buy_reason = None

        self.sell_time = None
        self.sell_price = None
        self.sell_reason = None
        self.sell_fees = None
        self.gain = None
        self.profit = None
        self.status = "OPEN"

    def addDeicsionLog(self, decision, msg):
        decision = DecisionLogEntry(self.current_price, decision, msg)
        self.decisionLog.append(decision)

    def updateCurrentPrice(self, current_price, current_price_dt=datetime.utcnow()):
        self.previous_price = self.current_price
        self.current_price = current_price

        if self.status != "OPEN":
            self.addDeicsionLog("ERROR", "Transaction is already closed")
            return

        # If price falls below stop loss price then sell
        if self.current_price < self.current_stop_loss_price:
            self.addDeicsionLog("SELL", "Current price falls below Stop loss price")
            self.sell(self.current_price)

        # If price crosses take profit then enable trailing stop loss
        if self.trailing_stop_loss_enabled == False and self.current_price > self.current_take_profit_price:
            self.trailing_stop_loss_enabled = True
            self.current_stop_loss_price = self.current_price * (100 - self.trailing_Stop_loss) / 100
            self.addDeicsionLog("HOLD", "Trailing stoploss enabled,take_profit=" + str(self.current_take_profit_price))
            return

        # If Price is above take profit price then updates
        if self.trailing_stop_loss_enabled == True and self.current_price > self.previous_price:
            self.current_stop_loss_price = self.current_price * (100 - self.trailing_Stop_loss) / 100
            self.addDeicsionLog("HOLD", "Reset stoploss price to " + str(self.current_stop_loss_price))
            return

    def sell(self, current_price):
        self.current_price = current_price
        self.closeTransaction(self.current_price, datetime.utcnow(), self.decisionLog[len(self.decisionLog) - 1].msg)

    def saveToDB(self):
        logging.debug("Inside Transaction.saveToDB")

    def closeTransaction(self, sell_price, sell_time, sell_reason):
        self.sell_price = sell_price
        self.sell_time = sell_time
        self.sell_reason = sell_reason

        # Calculate profit
        self.calculateFees()
        self.status = "CLOSE"

    def print(self):
        logging.info("Closing transaction")
        logging.info("Pair          :" + self.pair)
        logging.info("Quantity      :" + str(self.quantity))
        logging.info("Buy time      :" + self.buy_time.strftime(Constants.STANDARD_DATE_FORMAT))
        logging.info("Sell time     :" + self.sell_time.strftime(Constants.STANDARD_DATE_FORMAT))
        logging.info("Buy Price     :" + str(self.buy_price))
        logging.info("Sell Price    :" + str(self.sell_price))
        logging.info("Buy Reason    :" + self.buy_reason)
        logging.info("Sell Reason   :" + self.sell_reason)
        logging.info("Gain          :" + str(self.gain))
        logging.info("Profit        :" + str(self.profit))

    def getDictionary(self):
        dict = {}
        dict["status"] = self.status
        dict["pair"] = self.pair
        dict["key"] = self.key
        dict["quantity"] = self.quantity
        tmp_Datetime = Utilities.getDateTime(self.buy_time)
        dict["buy_time"] = tmp_Datetime.strftime(Constants.STANDARD_DATE_FORMAT)
        dict["buy_fees"] = self.buy_fees
        dict["buy_price"] = self.buy_price
        dict["buy_reason"] = self.buy_reason

        if self.sell_time is not None:
            tmp_Datetime = Utilities.getDateTime(self.sell_time)
            dict["sell_time"] = tmp_Datetime.strftime(Constants.STANDARD_DATE_FORMAT)
            dict["sell_price"] = self.sell_price
            dict["sell_reason"] = self.sell_reason
            dict["sell_fees"] = self.sell_fees
            dict["gain"] = self.gain
            dict["profit"] = self.profit

        return dict

    def calculateFees(self):
        if self.quantity is not None and self.buy_price is not None:
            self.buy_fees = self.quantity * self.buy_price * 0.1 / 100
            self.buy_cost = self.quantity * self.buy_price + self.buy_fees

        if self.quantity is not None and self.sell_price is not None:
            self.sell_fees = self.quantity * self.sell_price * 0.1 / 100
            self.gain = ((self.sell_price / self.buy_price) - 1) * 100
            self.profit = self.quantity * (self.sell_price - self.buy_price) - self.buy_fees - self.sell_fees
            self.final_amount = self.quantity * self.buy_price + self.profit

    def loadFromDictionary(self, dict):

        if dict is None:
            return;
        self.pair = dict["pair"]
        self.key = dict["key"]
        self.quantity = dict["quantity"]

        tmp_datetime = Utilities.getDateTime(dict["buy_time"])
        self.buy_time = tmp_datetime  # .strftime(Constants.STANDARD_DATE_FORMAT)
        self.buy_price = dict["buy_price"]
        self.buy_reason = dict["buy_reason"]

        if "sell_time" in dict.keys() and dict["sell_time"] is not None:
            tmp_datetime = Utilities.getDateTime(dict["sell_time"])
            self.sell_time = tmp_datetime  # datetime.strptime(dict["sell_time"], Constants.STANDARD_DATE_FORMAT)

        if "sell_price" in dict.keys() and dict["sell_price"] is not None:
            self.sell_price = dict["sell_price"]

        if "sell_reason" in dict.keys() and dict["sell_reason"] is not None:
            self.sell_reason = dict["sell_reason"]

        self.calculateFees()


#########################################################################################
class Portfolio:
    def __init__(self, dict):
        self.name = dict["name"]
        self.save_path = dict["save_path"]
        self.save_file_path = os.path.join(self.save_path, self.name + ".json")
        self.lstOpenTransactions = {}
        self.lstCloseTransactions = {}
        self.dict_heartbeat = {}
        self.total_profit = 0.0
        self.available_amount = 0.0
        self.save()

        PATH = "C:\\Users\\171802\\PycharmProjects\\Binance\\venv\\MessageQueue"
        mq = MQManager(PATH)
        exchange = mq.getExchange("Binance")
        self.heart_beat_consumer = exchange.getConsumer("heart_beat")
        self.transaction_consumer = exchange.getConsumer("Transactions")

    def run(self):
        print("inside Portfolio.run()")
        while (1 != 2):
            self.pollHeartBeat()
            # self.pollTransactions()
            time.sleep(3)

    def upsertTransaction(self, transaction):
        if transaction.status == "CLOSE":
            # Remove from open transaction ictionary
            self.removeOpenTransaction(transaction)

            # Add in close transactions
            self.addCloseTransaction(transaction)
        else:
            self.addOpenTransaction(transaction)

        self.save()

    def addCloseTransaction(self, transaction):
        self.lstCloseTransactions[transaction.key] = transaction
        self.total_profit = self.total_profit + transaction.profit
        self.available_amount = self.available_amount + transaction.final_amount

    def addOpenTransaction(self, transaction):
        self.lstOpenTransactions[transaction.key] = transaction
        self.available_amount = self.available_amount - transaction.buy_cost

    def removeOpenTransaction(self, transaction):
        if self.lstOpenTransactions.keys() is not None and transaction.key in self.lstOpenTransactions.keys():
            # Remove from open transaction
            self.lstOpenTransactions.pop(transaction.key)

    def calculatePortfolio(self):
        profit = 0.0
        for t in self.lstCloseTransactions:
            profit = profit + t.profit

        self.total_profit = profit

    def save(self):
        print("inside Portfolio.save()")
        dict = self.getDictionary()
        with open(self.save_file_path, 'w') as outfile:
            json.dump(dict, outfile, indent=4)

    def pollHeartBeat(self):
        try:
            print("inside Portfolio.pollHeartBeat()")
            lst_message = self.heart_beat_consumer.getMessageList(5000)
            if lst_message:
                for msg in lst_message:
                    # print("Key:{}, Message:{}, Ceation date:{}".format(msg.key, msg.message, msg.creation_date))
                    if msg.isValid:
                        self.processHeartBeat(msg.message)

            self.save()
        except:
            print("Error occured inPollHeartbeat")

    def pollTransactions(self):
        print("inside Portfolio.pollTransactions")
        lst_message = self.transaction_consumer.getMessageList(10000)
        if lst_message:
            for msg in lst_message:
                if msg.message is not None:
                    transaction = Transaction()
                    try:
                        transaction.loadFromDictionary(msg.message)
                        self.upsertTransaction(transaction)
                    except:
                        print("error occured while loading transaction")

    def processHeartBeat(self, msg):
        try:
            print("inside Portfolio.processHeartBeat()")
            id = msg["id"]
            dict_tmp = {}
            dict_tmp["update_time"] = msg["time"]
            dict_tmp["status"] = msg["status"]
            dict_tmp["current_price"] = msg["current_price"]
            dict_tmp["indicators_info"] = msg["indicators_info"]
            dict_tmp["current_amount"] = msg["current_amount"]
            self.dict_heartbeat[id] = dict_tmp
        except:
            print("Error occured while parsing message {}".format(msg))

    def getDictionary(self):
        dict = {}
        dict["total_profit"] = self.total_profit
        dict["available_amount"] = self.available_amount
        # Heart beat
        dict_temp = {}
        for k, t in self.dict_heartbeat.items():
            dict_temp[k] = t

        dict["heart_beat"] = dict_temp

        # Open transactions
        dict_temp = {}
        for k, t in self.lstOpenTransactions.items():
            dict_temp[k] = t.getDictionary()

        dict["open_transactions"] = dict_temp
        # Close transactions
        dict_temp = {}
        for k, t in self.lstCloseTransactions.items():
            dict_temp[k] = t.getDictionary()

        dict["close_transactions"] = dict_temp

        return dict

    def loadFromDictionary(self, dict):
        self.available_amount = dict["available_amount"]
        self.total_profit = dict["total_profit"]

        # load heart beats

        # load opentransactions

        # load close transactions


if __name__ == "__main__":
    p = Portfolio(
        {"name": "virtual", "save_path": "C:\\Users\\171802\\PycharmProjects\\Binance\\venv\\Database\\portfolio"})

    p.run()

    '''
    p = Portfolio({"name":"virtual","save_path":"C:\\Users\\171802\\PycharmProjects\\Binance\\venv\\Database\\portfolio"})

    trans_dict =  {}
    trans_dict["pair"] = "BTCEUR"
    trans_dict["key"] = "BTCEUR30m21_01_03_18_23_59"
    trans_dict["quantity"] = 80
    trans_dict["buy_time"] = datetime.now()
    trans_dict["buy_price"] = 1
    trans_dict["buy_reason"] = "Test reason"

    transaction = Transaction()
    transaction.loadFromDictionary(trans_dict)

    transaction.closeTransaction(1.1,datetime.now(),"test sell reason")
    p.upsertTransaction(transaction)
    '''

# TODO: Load portfolio from saved file
# TODO: Calculate total portfolio vlaues
# TODO: Show active and inactive bots