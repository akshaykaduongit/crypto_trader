import glob
import traceback
from datetime import datetime
import os
import json


class MQManager():
    def __init__(self, path):
        self.dict_exchange = {}
        self.path = path
        # os.chdir(self.path)
        print(os.getcwd())
        self.output_path = path
        self.config_path = os.path.join(self.output_path, "MQManager.json")
        self.loadFromFile()
        self.save()

    def loadFromFile(self):
        if not os.path.isfile(self.config_path):
            return

        with open(self.config_path) as config_file:
            dict = json.load(config_file)

        if "exchanges" in dict.keys():
            for k, d in dict["exchanges"].items():
                exchange = MQExchange(d["name"], d["type"], d["output_path"])
                self.dict_exchange[k] = exchange

    def createExchange(self, name, type):
        # Check if exchange name is already in use
        if name in self.dict_exchange:
            print("Exchange name already in use, could not create exchange")
            return None

        exchange = MQExchange(name, type, os.path.join(self.output_path, name))
        self.dict_exchange[name] = exchange
        self.save()
        return exchange

    def getExchange(self, name):
        return self.dict_exchange[name]

    def save(self):
        print(os.getcwd().capitalize())
        dict = self.getDictionary()
        print("config file path:" + self.config_path)
        print(dict)
        with open(self.config_path, 'w') as outfile:
            json.dump(dict, outfile, indent=4)

    def getDictionary(self):
        dict = {}
        dict["output_path"] = self.output_path
        dict["config_path"] = self.config_path
        dict_exchange = {}
        print("Current exchagne dictionary")
        # Loop through all exchanges
        for key, exchange in self.dict_exchange.items():
            print("---")
            print(type(exchange))
            d = exchange.getDictionary()
            print(type(d))
            dict_exchange[key] = d

        dict["exchanges"] = dict_exchange

        print(dict)
        return dict


#########################################################################################################
class MQExchange:
    def __init__(self, name, type, output_path):
        self.name = name
        self.type = type
        self.output_path = output_path
        self.save_path = os.path.join(output_path, "exchange.json")
        self.dict_queue = {}
        self.loadFromFile()
        self.save()

    def loadFromFile(self):
        if not os.path.isfile(self.save_path):
            return

        with open(self.save_path) as config_file:
            dict = json.load(config_file)

        if "dict_queue" in dict.keys():
            for k, d in dict["dict_queue"].items():
                queue = MQQueue(d["name"], self.output_path)
                self.dict_queue[k] = queue

    def registerQueue(self, queue_name):
        # function to register queue
        queue = MQQueue(queue_name, self.output_path)
        self.dict_queue[queue_name] = queue
        self.save()

    def getQueue(self, queue_name):
        if queue_name in self.dict_queue.keys():
            return self.dict_queue[queue_name]

    def deregisterQueue(self, queue):
        # function to de-register queue
        pass

    def getDictionary(self):
        dict = {}
        dict["name"] = self.name
        dict["type"] = self.type
        if self.output_path is not None:
            dict["output_path"] = self.output_path
            dict["save_path"] = self.save_path

        dict_queue = {}
        for k, d in self.dict_queue.items():
            dict_queue[k] = d.getDictionary()

        dict["dict_queue"] = dict_queue
        return dict

    def save(self):
        try:
            # Create directory if not exists
            if not os.path.exists(self.output_path):
                os.mkdir(self.output_path)

            dict = self.getDictionary()
            with open(self.save_path, 'w') as outfile:
                json.dump(dict, outfile, indent=4)
        except:
            traceback.print_exc()

    def getConsumer(self, name):
        if name in self.dict_queue.keys():
            return MQConsumer(self, name)
        else:
            return None

    def getProducer(self):
        return MQProducer(self)

    def postMessage(self, msg):
        try:
            queue_name = msg.key
            if queue_name in self.dict_queue.keys():
                q = self.dict_queue[queue_name]
                # q = MQQueue(msg.key,self.output_path)
                q.addMessage(msg)
            else:
                print("Queue not present")
        except:
            traceback.print_exc()


#########################################################################################################
class MQMessage:

    def __init__(self):
        self.key = None
        self.message = None
        self.creation_date = None
        self.isValid = False

    def loadFromDict(self, dict):
        # TODO: check if msg is dictionary
        print("inside MQMessage>loadFromDict")
        print("Key:{},msg:{},PAramener={}".format(dict["key"], dict["message"], dict))

        self.key = dict["key"]
        self.creation_date = str(datetime.timestamp(datetime.utcnow()))
        self.message = dict["message"]

        print(self.message)
        print("Message dictionary:{}".format(self.getDictionary()))

    def loadFromFile(self, file_path):
        try:
            # TODO : load message object from file
            # Leave if file does not exist
            if not os.path.isfile(file_path):
                print("Message file not found")
                return

            dict = {}
            with open(file_path) as config_file:
                print(file_path)
                dict = json.load(config_file)

            self.key = dict["key"]
            self.message = dict["message"]
            self.creation_date = dict["creation_date"]
            self.isValid = True
        except:
            print("Some error occured whild reading json - {}".format(file_path))

    def getDictionary(self):
        print("inside MQMessage>GetDictionary")
        dict = {}
        dict["key"] = self.key
        dict["creation_date"] = self.creation_date
        dict["message"] = self.message
        return dict


#########################################################################################################
class MQProducer:
    def __init__(self, exchange):
        self.exchange = exchange

    def postMessage(self, key, dict_msg):
        try:
            print("inside MQProducer > postMessage()")
            print("message body:{}".format(dict_msg))
            msg = MQMessage()
            msg.loadFromDict({"key": key, "message": dict_msg})
            self.exchange.postMessage(msg)
            print("Message object dictionary:{}".format(msg.getDictionary()))
        except:
            traceback.print_exc()


########################################################################################################
class MQConsumer:
    def __init__(self, exchange, queue_name):
        self.exchange = exchange
        self.queue_name = queue_name

    def getMessage(self):
        queue = self.exchange.getQueue(self.queue_name)
        path = queue.output_path
        print("Queue path:" + path)

        # Check if message exists
        os.listdir(queue.output_path)
        dirs = os.listdir(queue.output_path)
        if len(dirs) == 0:
            return None

        oldest_file = \
        sorted([os.path.join(queue.output_path, f) for f in os.listdir(queue.output_path)], key=os.path.getctime)[0]
        # print(type(oldest_file))
        # print("oldest file:"+oldest_file)

        msg = MQMessage()
        msg.loadFromFile(oldest_file)

        os.remove(oldest_file)
        return msg

    def getMessageList(self, limit):
        queue = self.exchange.getQueue(self.queue_name)
        path = queue.output_path
        print("Queue path:" + path)

        # Check if message exists
        os.listdir(queue.output_path)
        dirs = os.listdir(queue.output_path)
        if len(dirs) == 0:
            return None

        oldest_file = sorted([os.path.join(queue.output_path, f) for f in os.listdir(queue.output_path)],
                             key=os.path.getctime)
        lst_files = []

        lst_message = []
        count = 0
        for m in oldest_file:
            msg = MQMessage()
            msg.loadFromFile(m)
            lst_message.append(msg)
            lst_files.append(m)
            count = count + 1
            if count == limit:
                break

        # Remove message files
        for m in lst_files:
            os.remove(m)

        return lst_message

    def postMessage(self, msg):
        self.exchange.postMessage(msg)


#########################################################################################################
class MQQueue:
    def __init__(self, name, output_path):
        self.name = name
        self.output_path = os.path.join(output_path, self.name)
        self.createFolder()

    def createFolder(self):
        if os.path.exists(self.output_path):
            return

        os.mkdir(self.output_path)

    def addMessage(self, message):
        print("inside MQQueue > addMessage()")
        print("Message key:" + message.key)
        dict = message.getDictionary()
        print(dict)
        file_name = os.path.join(self.output_path, message.creation_date + ".json")
        print(file_name)
        with open(file_name, 'w') as outfile:
            json.dump(dict, outfile, indent=4)

    def getMessage(self):
        pass

    def getDictionary(self):
        return self.__dict__


#########################################################################################################
# Code starts here
if __name__ == '__main__':

    PATH = "C:\\Users\\171802\\PycharmProjects\\Binance\\venv\\MessageQueue"
    mq = MQManager(PATH)
    exchange = mq.getExchange("Test")
    producer = exchange.getProducer()
    print("Posting message")
    msg_dict = {"fname": "akshay", "lname": "kadu"}
    producer.postMessage("Transactions", msg_dict)
    producer.postMessage("Transactions", msg_dict)
    producer.postMessage("Transactions", msg_dict)
    producer.postMessage("Transactions", msg_dict)
    producer.postMessage("Transactions", msg_dict)
    producer.postMessage("Transactions", msg_dict)
    producer.postMessage("Transactions", msg_dict)

    consumer = exchange.getConsumer("Transactions")
    lst_message = consumer.getMessageList(200)
    print(len(lst_message))
    if lst_message:
        for msg in lst_message:
            print("key:{},message:{},ceation date:{}".format(msg.key, msg.message, msg.creation_date))

    # exchange = mq.createExchange("Binance","Key")
    # exchange.registerQueue("heart_beat")
    # exchange = mq.createExchange("Test","Key")

    # exchange = mq.getExchange("Binance")
    # exchange.registerQueue("Transactions")

    # Post message
    # producer = exchange.getProducer()
    # print("Posting message")
    # msg_dict = {"fname":"akshay","lname":"kadu"}
    # producer.postMessage("Transactions",msg_dict)

    # consumer = exchange.getConsumer("Transactions")
    # msg = consumer.getMessage()
    # while msg is not None:
    #    print("key:{},message:{},ceation date:{}".format(msg.key,msg.message,msg.creation_date))
    #    msg = consumer.getMessage()

'''
    dirs = os.listdir("C:\\Users\\171802\\PycharmProjects\\Binance\\venv\\MessageQueue\\Test\\Transactions")
    print(type(dirs))
    print(len(dirs))

'''