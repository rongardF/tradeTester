import threading
import traceback

from datetime import datetime as dt
from tvDatafeed import Interval
from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
from livetrader.sqlManager import sqlManager
from livetrader.testruns import testrunsManager, testrunData
from livetrader.orders import orderData

class asset_set(object):
    
    def __init__(self, symbol=None, exchange=None, intervals=[]): # intervals must be a list of objects
        self.symbol=symbol
        self.exchange=exchange
        self.intervals=intervals
    
    def set_symbol(self, symbol):
        '''
        Set the symbol for this asset, input is string. Old value will be overvwritten
        '''
        self.symbol=symbol
    
    def get_symbol(self):
        '''
        Get the asset symbol
        '''
        return self.symbol
    
    def set_exchange(self, exchange):
        '''
        Set the exhcange/market where this symbol is traded
        '''
        self.exchange=exchange
    
    def get_exchange(self):
        '''
        Get the exchange/market for this symbol
        '''
        return self.exchange
    
    def add_interval(self, interval):
        '''
        Add another timeframe for this symbol. This class will contain a list of timeframes (bars) for this symbol
        '''
        self.intervals.append(interval)
    
    def get_intervals_string(self):
        '''
        Return a list of intervals as a string.
        '''
        list_str=""
        for inter in self.intervals:
            list_str=list_str+" "+str(inter)
        
        return list_str
    
    def __iter__(self): 
        '''
        Iter method to return iterator and also reset all iteration related attributes
        '''
        self.asset_sets=[] # get a list of all testruns
        for inter in self.intervals:
            asset_set=[self.symbol, self.exchange, inter]
            self.asset_sets.append(asset_set)
            
        self.iter_index=0 # reset  list index
        self.iter_stop=len(self.asset_sets) # set stopping value
        return self
    
    def __next__(self):
        '''
        Next method to iterate over all asset_sets (combinations with Interval) - return will be a list of [symbol, exchange, interval]
        '''
        if self.iter_index >= self.iter_stop:
            raise StopIteration
        else:
            iter_val=self.asset_sets[self.iter_index]
            self.iter_index+=1 # increment index
            return iter_val
    
    
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
    
    def strToIntervals(self, inter_str):
        intervals=[]
        for inter in inter_str.split():
            intervals.append(eval(inter))
            
        return intervals
    
    def get_ticker_data(self, TUID):
        '''
        Retrieve ticker data. TUID specifies the testrun from which we get asset_id.
        
        Ticker data is returned in list of DataFrames
        '''
        ticker_data_list=[]
        
        sql_testruns=self.sql.read_testruns()
        for testrun in sql_testruns:
            if testrun[0] == TUID: # this is the testrun for which we want ticker data
                asset_aid=self.testruns.get_testrun(testrun[0]).get_asset_aid() # get asset_aid by retrieving testrun from testrunsManager and getting its asset_id attribute
                break 
        
        for asset_id in asset_aid:
            ticker_data_list.append(self.sql.read_ticker_data(asset_id)) # get ticker data (DataFrame) and put it into list of Pandas DataFrames 
        
        return ticker_data_list
        
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
            if testrun[4] == "NULL": # if testrun is not closed then we don't have close datetime
                stop_dt="N/A"
            else:
                stop_dt=dt.strptime(testrun[4],"%Y-%m-%d %H:%M:%S")
                
            testruns_list.append(testrunData(testrun[0], testrun[1], testrun[2],\
                                              dt.strptime(testrun[3],"%Y-%m-%d %H:%M:%S"), \
                                              stop_dt, \
                                              testrun[5], testrun[6], self.strToIntervals(testrun[7]), \
                                              testrun[8], testrun[9]))
        
        return testruns_list
    
    def start_testrun(self, testrun_name, strategy, asset, account_size):
        '''
        Start a new testrun with provided strategy
        '''
        TUID=self.testruns.new_testrun(testrun_name, strategy, asset, account_size, self.exception_handler)
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
        asset_aid=self.testruns.get_testrun(TUID).get_asset_aid() # get the asset_id for this testrun based on TUID
        self.sql.set_streamer(TUID, asset_aid) # data for ths TUID and asset_id must be propagated to GUI
