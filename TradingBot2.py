import os
from datetime import datetime
from Constants import Constants
class TradingBot2:
    def __init__(self, name, quote_symbol):
        self.name = name
        self.quote_symbol = quote_symbol
        self.dict_main = {}
        self.dict_main["name"] = self.name
        self.dict_main["quote_symbol"] = self.quote_symbol

        dict_current_state = {}
        dict_current_state["deposit_amount"]    = 0.0 # Total depoited amount
        dict_current_state["current_amount"]    = 0.0 # Total amount available for trading
        dict_current_state["invested_amount"]   = 0.0 # Total invested amount
        dict_current_State["reserved_amount"]   = 0.0 # Amount reserved to be withdraw
        dict_Current_state["withdraw_amount"]   = 0.0 #AMount withdraed from account

        self.dict_main["current_State"] = self.dict_current_state

        # load list of pairs
        # list of open transactions
        # lilst of closed transactions
        # total amount
        # total profit
        # percentage profit
        # total wins count
        # total loss count

        dict_open_transactions = {}
        lst_closed_transaction = []
        lst_deposit_log = []
        lst_withdrawl_log = []

        dict_logs = {}
        dict_logs["closed_transactions"] = []
        dict_logs["deposit_log"] = []
        dict_logs["withdrawl_log"] = []
        dict_logs["reserved_log"] = []

        self.dict_main["logs"] = dict_logs

    def deposit(self, amt):
        try:
            dict_current_state = self.dict_main["dict_current_state"]
            dict_current_state["deposit_amount"] = dict_current_state["deposit_amount"] + amt
            dict_current_state["current_amount"] = dict_current_state["current_amount"] + amt
            self.dict_main["dict_current_state"] = dict_current_state

            # Create deposit log
            dict_log = {}
            dict_log["update_time"] = datetime.now().strftime(Constants.Constants.STANDARD_DATE_FORMAT)
            dict_log["amount"] = amt
            lst_deposit_log = self.dict_main["logs"]["deposit_log"]
            lst_deposit_log.append(dict_log)
            self.dict_main["logs"]["deposit_log"] = lst_deposit_log

        except:
            print("Error occured in TradingBot2>deposit")

    def withdraw(self, amt):
        try:
            dict_current_state = self.dict_main["dict_current_state"]
            tmp = self.dict_current_state["current_amount"]
            tmp_res = self.dict_current_state["reserved_amount"]
            if amt > (tmp_res+tmp):
                print("Current amount is less than withdraw amount")
                return

            if amt > tmp_res:
                dict_current_state["reserved_amount"] = 0.0
                dict_current_state["current_amount"] = tmp-(amt-tmp_res)

            else:
                dict_current_state["reserved_amount"] = dict_current_state["reserved_amount"] - amt

            dict_current_state["withdraw_amount"] = dict_current_state["withdraw_amount"] + amt

            self.dict_main["dict_current_state"] = dict_current_state

        except:
            print("Error occured in TradingBot2>withdraw")

    def addBaseCoin(self,base_symbol):
        pass

    def reserveAmount(self):
