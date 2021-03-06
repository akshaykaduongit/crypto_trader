import logging
import statistics

class OHLC:
    def __init__(self,open,high,low,close,volume):
        self.open   = open
        self.high   = high
        self.low    = low
        self.close  = close
        self.volume = volume

    def print(self):
        print("Open     :" + str(self.open))
        print("high     :" + str(self.high))
        print("low      :" + str(self.low))
        print("close    :" + str(self.close))
        print("volume   :" + str(self.volume))

class MFI:
    def __init__(self,window):
        self.window = window
        self.count = 0
        self.positive_flow = 0.0
        self.negative_flow = 0.0
        self.mfi = 0.0
        self.status = "open"
        self.prev_typical_price = 0.0
        self.money_flow_index = 100.0
        self.stdev = 0.0
        self.mean = None
        self.lst_ohlc = []

    def add_entry(self, ohlc):

        # print ("adding - "+str(ohlc.timestamp))
        if self.status == "close":
            return

        self.lst_ohlc.append(ohlc)
        typical_price = (ohlc.high + ohlc.low + ohlc.close) / 3
        abs_raw_money_flow = typical_price * ohlc.volume

        #First entry
        if self.count == 0:
            self.prev_typical_price = typical_price
            self.count = self.count + 1
            # print("First entry")
            return

        self.count = self.count + 1
        # print("prev_price\ttypical_price")
        # print(str(self.prev_typical_price) + "\t"+str(ohlc.typical_price))

        if self.prev_typical_price <= typical_price:
            self.positive_flow = self.positive_flow + abs_raw_money_flow
        #  print (str(ohlc.timestamp)+" addign to positive flow - \t "+str(ohlc.abs_raw_money_flow))
        else:
            self.negative_flow = self.negative_flow + abs_raw_money_flow
        #  print (str(ohlc.timestamp)+" addign to negative flow - \t "+str(ohlc.abs_raw_money_flow))

        self.prev_typical_price = typical_price
        if self.count == self.window+1:
            #Calculate MFI
            #print("Reached window limit"+str(self.window))
            if self.negative_flow == 0:
                self.money_flow_index = 100
            else:
                self.money_flow_ratio = self.positive_flow / self.negative_flow
                self.money_flow_index = 100 - (100 / (1 + self.money_flow_ratio))

            #Calculate Standard deviation
            lst_close_values = []
            for h in self.lst_ohlc:
                lst_close_values.append(h.close)

            self.stdev = statistics.stdev(lst_close_values)
            self.mean = statistics.mean(lst_close_values)
            self.status = "close"

class Indicators:
    def getMFI(self, lst_ohlc,MFIPeriod):
        lst_ohlc2 = lst_ohlc.copy()
        count = 0
        lst_ohlc_tmp = []
        lst_ohlc_output = []
        for o1 in lst_ohlc2:
            mfi = 0.0
            lst_ohlc_tmp.append(o1)
            if len(lst_ohlc_tmp) == MFIPeriod+1:
                o_mfi = MFI(MFIPeriod)
                for t in lst_ohlc_tmp:
                    o_mfi.add_entry(t)

                mfi = o_mfi.money_flow_index
                o1.mfi = mfi
                o1.stdev = o_mfi.stdev
                o1.mean = o_mfi.mean
                lst_ohlc_output.append(o1)
                del lst_ohlc_tmp[0]

        return lst_ohlc_output

class MFISignal:
    def __init__(self, time, previous_value, new_value, current_price):
        self.time = time
        self.previouosMFI = previous_value
        self.newMFI = new_value
        self.currentPrice = current_price
        self.signalType = ""
        self.signalType = self.getState(self.previouosMFI) + "-"+self.getState(self.newMFI)

    def getState(self,val):
        if val<20:
            return "OVERSOLD"

        if val>80:
            return "OVERBOUGHT"

        return "NORMAL"