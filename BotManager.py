from TradingBot import TradingBot
import configparser
import json
import threading
import os

class BotManager:

    def __init__(self):
        self.dict_bots = {}

    def loadBotsFromConfig(self):
        print("Reading data from config_pair_list.json")
        with open(os.path.join("config","config_pair_list.json")) as config_file:
            self.dict_bots = json.load(config_file)

    def startBots(self):
        self.loadBotsFromConfig()
        #with open(".\\config\\config_pair_list.json") as config_file:
        #    dictBots = json.load(config_file)
        threads = []

        for d in self.dict_bots['bots']:

            tb = TradingBot(d)
            #tb.loadFromJsonFile()
            tb.is_active = True
            tb.start()
            threads.append(tb)

        # Wait for all threads to complete
        for t in threads:
            t.join()
            time.sleep(120)
            #self.createSummaryJson()

def createSummaryJson(self):
    # loop through each file in bot_Stats folder
    dirs = os.listdir(queue.output_path)
    # Populate dictionary
    rootdir = os.path.join("Database","bots_state")
    extensions = ('.json')

    dict_summary = {}
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext in extensions:
                with open(os.path.join(subdir, file)) as bot_file:
                    dict = json.load(bot_file)
                    dict_temp = {}
                    key = "{}{}".format(dict["base_symbol"],dict["quote_symbol"])
                    dict_temp["initial_amount"]=dict["initial_amount"]
                    dict_temp["current_amount"] = dict["current_amount"]
                    dict_temp["status"] = dict["status"]
                    dict_temp["type"] = dict["type"]
                    dict_summary[key]= dict_temp

    with open(os.path.join("Database","bot_summary.json"), 'w') as outfile:
        json.dump(dict_summary, outfile, indent=4)






# Code starts here
bot_manager = BotManager()
bot_manager.startBots()

# TODO: Stop all bots
# TODO: Stop sepcific bot
# TODO: Sell all bots
# TODO: Sell specific bot