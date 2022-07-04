'''
'''

from datetime import datetime as dt
from livetrader.strategyRunner import strategyRunner as strategy_runner

class testruns(object):
    
    def __init__(self, data_collector, sql): # user can specify the starting value for order_id (incase we are going from backtest to forward test)
        self.data_collector=data_collector
        self.sql=sql
        self.sql_input, self.sql_output=self.sql.get_io()
        self.testruns_dict={}
    
    def is_name_used(self, name): # check that we do not have a testrun/strategy with this name in the dictionary
        for testruns_list in self.testruns_dict.values():
            # if name in strat_names_list:
            #     return False
            for testrun in testruns_list:
                if name == testrun.name:
                    return True
        return False
    
    def exception_handler(self, e, TUID):
        testrun=self.get_testrun(TUID)
        testrun.close_testrun() # close down testrun
        self.sql.close_testrun(testrun) # close testrun in database and also close streamer
        if not self.is_asset_used(testrun.asset_id): # is asset not used by any other testruns
            self.data_collector.del_symbol(testrun.asset_id)
        testrun.exception_callback(e, TUID) # call the callback provided by the user (controller.py)
    
    def new_testrun(self, testrun_name, strategy, symbol, exchange, interval, account_size, exception_callback):  
        if self.is_name_used(testrun_name): # if name is used then return None which informs user
            return None
        
        asset_id=self.data_collector.add_symbol(symbol, exchange, interval) # get ID for this asset set - it might already exists in data_collector
        new_testrun=testrun(testrun_name, dt.now().strftime("%d-%m-%y %H:%M"), \
                            symbol, exchange, str(interval), asset_id, account_size, exception_callback) # opposite operation is datetime_obj=dt.strptime(start_dt_str,"%d-%m-%y %H:%M")
        new_testrun=self.sql.add_testrun(new_testrun) # add testrun into SQL database and assign TUID for testrun
        TUID=new_testrun.get_TUID()
        strat_ref=strategy_runner(self.data_collector, self.sql_input, TUID, asset_id, strategy, self.exception_handler) # SOMEHOW HAVE TO ENTER THE SQL_INPUT FOR STRATEGY INSTANCE
        new_testrun.add_strat_ref(strat_ref)
        if asset_id in self.testruns_dict.keys(): # if already existing then just append testrun reference
            self.testruns_dict[asset_id].append(new_testrun)
        else: # need to create a new key-value pair and add it into new list
            self.testruns_dict[asset_id]=[new_testrun]
        strat_ref.start() # start the strategy in that testrun
        # else:
        #     raise ValueError("Strategy with this name already running") 
        
        return TUID
    
    def close_testrun(self, TUID):
        testrun=self.get_testrun(TUID) # get testrun object based on TUID
        if testrun.state == "OPEN": # check that it hasn't already been closed (by exception handler)
            # asset_id=testrun.get_asset_id()
            # TUID=testrun.get_TUID()
            testrun.close_testrun() # change the testrun status
            self.sql.close_testrun(testrun) # close testrun in database and also close streamer
            testrun.get_strat_ref().stop() # stop the strategyRunner instance for this strategy
            #self.remove_testrun(asset_id, TUID) # remove the testrun from the list of active testruns
        
        if not self.is_asset_used(testrun.asset_id): # is asset not used by any other testruns
            self.data_collector.del_symbol(testrun.asset_id)
            
    def get_testrun(self, TUID):
        for testruns_list in self.testruns_dict.values():
            for testrun in testruns_list:
                if TUID == testrun.TUID:
                    return testrun
        
        return None # if no such testrun exists 
    
    def is_asset_used(self, asset_id):
        '''
        Check if this asset set is used by any testruns
        '''
        for testruns_list in self.testruns_dict.values():
            for testrun in testruns_list:
                if (testrun.asset_id == asset_id) and (testrun.state == "OPEN"): # uses this asset set and is open
                    return True 
        
        return False
    
class testrun(object):
    
    def __init__(self, testrun_name, start_datetime, symbol, exchange, interval, asset_id, starting_account, exception_callback):
        self.TUID=None
        self.name=testrun_name
        self.state="OPEN"
        self.start_datetime=start_datetime
        self.close_datetime="NULL"
        self.symbol=symbol
        self.exchange=exchange
        self.interval=interval
        self.asset_id=asset_id
        self.starting_account=starting_account
        self.closing_account="NULL"
        self.strat_ref=None
        self.exception_callback=exception_callback
        
    def close_testrun(self):
        self.state="CLOSED"
        self.close_datetime=dt.now().strftime("%d-%m-%y %H:%M")
        #self.close_callback(self.asset_id, self)
    
    def get_sql_params(self):
        if self.state == "OPEN":
            return (self.name, self.state, self.start_datetime, self.close_datetime, self.symbol, \
                    self.exchange, self.interval, self.starting_account, self.closing_account)
        else:
            return (self.state, self.close_datetime, self.TUID)
    
    def set_TUID(self, TUID):
        self.TUID=TUID
    
    def get_TUID(self):
        return self.TUID
    
    def get_asset_id(self):
        return self.asset_id
    
    def add_strat_ref(self, ref):
        self.strat_ref=ref
        
    def get_strat_ref(self):
        return self.strat_ref
