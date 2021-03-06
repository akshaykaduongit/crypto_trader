#from TradingBot import TradingBot
import os
import json
import time
from Constants import Constants
from datetime import datetime

def createSummaryJson():
    # loop through each file in bot_Stats folder
    #dirs = os.listdir(queue.output_path)
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
                    key = "{}{}_{}".format(dict["base_symbol"],dict["quote_symbol"],dict["type"])
                    dict_temp["initial_amount"]=dict["initial_amount"]
                    dict_temp["current_amount"] = dict["current_amount"]
                    dict_temp["status"] = dict["status"]
                    dict_temp["type"] = dict["type"]
                    dict_temp["update_time"] = dict["update_time"] 
                    dict_summary[key]= dict_temp

    dict_root = {}
    dict_root["update_time"]= datetime.now().strftime(Constants.STANDARD_DATE_FORMAT)
    dict_root["bot_list"]= dict_summary
    with open(os.path.join("Database","bot_summary.json"), 'w') as outfile:
        json.dump(dict_root, outfile, indent=4)

    print("{}:Population of bot summary commpleted".format(datetime.utcnow().strftime(Constants.STANDARD_DATE_FORMAT)))

createSummaryJson()

