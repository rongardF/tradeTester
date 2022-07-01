import threading
import traceback
from datetime import datetime as dt

from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
from livetrader.sqlManager import sqlManager
from livetrader.testruns import testruns

class controller(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, sql_path):
        '''
        Constructor
        '''
        self.data_collector=tdr()
        self.sql=sqlManager(sql_path) 
        self.sql_input, self.sql_output=self.sql.get_io()
        self.sql.start()
        self.testruns=testruns(self.data_collector, self.sql) 

        threading.Thread.__init__(self)
        
    def run(self):
        while True:
            pass
    
    def exception_handler(self, e, TUID):
        '''
        Handle exceptions that might have been thrown in any of the testruns
        '''
        print("Exception from "+str(TUID))
        traceback.print_exception(e)
        
    def get_testruns(self):
        '''
        Return a list of all the strategies (running and stopped)
        '''
        name_list=[]
        testruns=self.sql.read_testruns()
        for testrun in testruns:
            name_list.append(testrun[1])
        
        return name_list
    
    def start_testrun(self, testrun_name, strategy, symbol, exchange, interval, account_size):
        '''
        Start a new testrun with provided strategy
        '''
        TUID=self.testruns.new_testrun(testrun_name, strategy, symbol, exchange, interval, account_size, self.exception_handler)
        return TUID
    
    def stop_testrun(self, TUID):
        '''
        Stop strategy from running
        '''
        self.testruns.close_testrun(TUID) # get the testrun object
    
    def stop_all_testruns(self):
        '''
        Stop all strategies from running - this is called before closign down tradeTester application
        '''
        pass
    
    def del_testrun(self):
        '''
        Remove testrun from the list and all related data
        '''
        raise NotImplemented
    
    def select_testrun(self, TUID):
        '''
        Configure which testrun data is propagated to GUI
        '''
        asset_id=self.testruns.get_testrun(TUID).asset_id # get the asset_id for this testrun based on TUID
        self.sql.set_streamer(TUID, asset_id) # data for ths TUID and asset_id must be propagated to GUI
