from datetime import datetime
import Constants
import job_binance_download
#Scheduler config file will have following information
# 1. JOB NAME (IDENTIFIER)
# 2. JOB interval (in seconds)
# 3. JOB script


class Scheduler:
    def __init__(self,folder_path):
        #folder_path = folder where Scheduler will save state and other required files for working
        self.dict_config = {}
        self.dict_job_list = {}
        self.dict_last_run_times = {}
        self.status = 'INACTIVE'

    #This function will start the scheduler jobs according to configuration
    def start(self):
        pass

    #Function to stop scheduler
    def stop(self):
        pass

    def run(self):

        while self.status=='ACTIVE':
            # Loop through


            # Check for State file
            self.checkForStateFile()

    # Fetch last run time and check if job needs to run
    def isDueToRun(self,job_name):
        last_run_time = datetime.strptime(self.dict_last_run_times[job_name],Constants.STANDARD_DATE_FORMAT)
        diff = (datetime.now()-last_run_time).total_seconds()


    #This function will check for TOP file.  If fileis present then scheduler will run otherwise it will stop
    def checkForStateFile(self):
        pass

    #Function to read config file
    def readConfigFile(self):
        pass

    #Function to trigger job
    def triggerJob(self):
        pass

