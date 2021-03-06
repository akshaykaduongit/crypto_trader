from datetime import datetime
from Constants import Constants

class Utilities:
    @staticmethod
    def getDateTime(parameter):
        if type(parameter) == str:
            return datetime. strptime(parameter, Constants.STANDARD_DATE_FORMAT)
        else:
            return parameter

class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.status = "OFF"

    def start(self):
        self.start_time = datetime.now()
        self.status = "ON"

    def end(self):
        self.end_time = datetime.now()
        self.status = "OFF"

    def getTimeInSeconds(self):
        if self.status == "OFF":
            return (self.end_time-self.start_time).total_seconds()
        else:
            return None

if __name__ == "__main__":
    var = datetime.now()
    var2 = Utilities.getDateTime(var)
    print(type(var2))
