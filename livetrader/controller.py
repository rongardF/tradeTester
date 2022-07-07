import threading
import traceback

from datetime import datetime as dt
from tvDatafeed import Interval
from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
from livetrader.sqlManager import sqlManager
from livetrader.testruns import testrunsManager, testrunData
from livetrader.orders import orderData

class controller(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, sql_path):
        '''
        Constructor
        '''
        self.data_collector=tdr(True) # each new asset_id will be unique and old, removed asset sets IDs will not be re-used
        self.sql=sqlManager(sql_path) 
        self.sql_input, self.sql_output=self.sql.get_io()
        self.sql.start()
        self.testruns=testrunsManager(self.data_collector, self.sql) 

        threading.Thread.__init__(self)
        
        self.str2inter={"1 minute":Interval.in_1_minute, "3 minutes":Interval.in_3_minute, \
                        "5 minutes":Interval.in_5_minute, "15 minutes":Interval.in_15_minute, \
                        "30 minutes":Interval.in_30_minute, "45 minutes":Interval.in_45_minute, \
                         "1 hour":Interval.in_1_hour, "2 hours":Interval.in_2_hour, "3 hours":Interval.in_3_hour, \
                         "4 hours":Interval.in_4_hour, "1 day":Interval.in_daily, "1 week":Interval.in_weekly, \
                         "1 month":Interval.in_monthly}
        
        self.inter2str={"Interval.in_1_minute":"1 minute","Interval.in_3_minute":"3 minutes", \
                        "Interval.in_5_minute":"5 minutes", "Interval.in_15_minute":"15 minutes", \
                        "Interval.in_30_minute":"30 minutes", "Interval.in_45_minute":"45 minutes", \
                        "Interval.in_1_hour":"1 hour", "Interval.in_2_hour":"2 hours", "Interval.in_3_hour":"3 hours", \
                        "Interval.in_4_hour":"4 hours", "Interval.in_daily":"1 day", "Interval.in_weekly":"1 week", \
                        "Interval.in_monthly":"1 month"}
        
    def run(self):
        while True:
            pass
    
    def exception_handler(self, e, TUID):
        '''
        Handle exceptions that might have been thrown in any of the testruns
        '''
        print("Exception from "+str(TUID))
        traceback.print_exception(e)
    
    def __str2interval(self, inter_str):
        if inter_str in self.str2inter:
            return self.str2inter[inter_str]
        else:
            raise ValueError("No such interval string")
        
    def __interval2str(self, interval):
        if interval in self.inter2str:
            return self.inter2str[interval]
        else:
            raise ValueError("No such interval")
        
    def get_orders(self, TUID):
        '''
        Return a list of order_data objects for all the orders for this particular testrun (TUID)
        '''
        orders_list=[]
        orders=self.sql.read_orders(TUID)
        for order in orders:
            if order[4] == "NULL":
                stop_dt="N/A"
            else:
                stop_dt=dt.strptime(order[4],"%Y-%m-%d %H:%M:%S")
                
            orders_list.append(orderData(order[0], order[2], dt.strptime(order[3],"%Y-%m-%d %H:%M:%S"), \
                                              stop_dt, order[5], order[6], order[7], \
                                              order[8], order[9], order[9]))
        
        return orders_list
    
    def get_testruns(self):
        '''
        Return a list of testrun_data objects for all the testruns in database (running and stopped) 
        '''
        testruns_list=[]
        testruns=self.sql.read_testruns()
        for testrun in testruns:
            if testrun[4] == "NULL":
                stop_dt="N/A"
            else:
                stop_dt=dt.strptime(testrun[4],"%Y-%m-%d %H:%M:%S")
                
            testruns_list.append(testrunData(testrun[0], testrun[1], testrun[2],\
                                              dt.strptime(testrun[3],"%Y-%m-%d %H:%M:%S"), \
                                              stop_dt, \
                                              testrun[5], testrun[6], self.__interval2str(testrun[7]), \
                                              testrun[8], testrun[9]))
        
        return testruns_list
    
    def start_testrun(self, testrun_name, strategy, symbol, exchange, interval, account_size):
        '''
        Start a new testrun with provided strategy
        '''
        TUID=self.testruns.new_testrun(testrun_name, strategy, symbol, exchange, self.__str2interval(interval), account_size, self.exception_handler)
        return TUID
    
    def stop_testrun(self, TUID):
        '''
        Stop strategy from running
        '''
        if self.testruns.get_testrun(TUID) is not None: # check first that such a testrun exists
            self.testruns.close_testrun(TUID) # get the testrun object
    
    def stop_all_testruns(self):
        '''
        Stop all strategies from running - this is called before closing down tradeTester application
        '''
        self.testruns.close_all_testruns()
    
    def del_testrun(self, TUID):
        '''
        Remove testrun from the list and all related data
        '''
        self.stop_testrun(TUID) # first stop the testrun from running
        self.testruns.del_testrun(TUID)
    
    def select_testrun(self, TUID):
        '''
        Configure which testrun data is propagated to GUI
        '''
        asset_id=self.testruns.get_testrun(TUID).asset_id # get the asset_id for this testrun based on TUID
        self.sql.set_streamer(TUID, asset_id) # data for ths TUID and asset_id must be propagated to GUI
