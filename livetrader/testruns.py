'''
Rename the testruns and testrunsManager classes; rename orders to ordersManager as well
Test the new stuff out
'''

from datetime import datetime as dt
from livetrader.strategyRunner import strategyRunner as strategy_runner
from livetrader.sqlManager import operations, packet

class testrunData(object):
    
    def __init__(self, TUID, name, state, start_dt, close_dt, symbol, exchange, interval, starting_account, closing_account):
        self.TUID=TUID
        self.name=name
        self.state=state
        self.start_datetime=start_dt
        self.close_datetime=close_dt
        self.symbol=symbol
        self.exchange=exchange
        self.interval=interval
        self.starting_account=starting_account
        self.closing_account=closing_account

class testrunManager(object):
    ''' 
    Track and manage all testruns in reference to asset_id
    '''
    def __init__(self):
        self.testruns={} # dictionary holding all testruns grouped by asset_id
        self.callback_refs={} # dictionary holding callback references for each asset_id
    
    def add_testrun(self, testrun):
        '''
        Add testrun into register. If no such asset_id group exists then it will be created
        '''
        asset_id=testrun.get_asset_id()
        if asset_id not in self.testruns:
            self.testruns[asset_id]=[]
        
        self.testruns[asset_id].append(testrun)
    
    def del_testrun(self, TUID):
        ''' 
        Delete testrun from register tracking all the testruns
        '''
        testrun=self.get_testrun(TUID)
        asset_id=testrun.asset_id
        self.testruns[asset_id].remove(testrun) # remove testrun from the list
        if not self.testruns[asset_id]: # no more testruns for this asset_id remove asset_id group from dictionary
            del self.testruns[asset_id]
            if asset_id in self.callback_refs: # if callback was added for this asset then remove it
                del self.callback_refs[asset_id]

    def set_asset_callback_ref(self, asset_id, callback_ref):
        '''
        Add a tvDatafeedRealtime callback reference for this asset_id
        '''
        if asset_id not in self.testruns:
            raise KeyError("No such asset listed")
        else:
            self.callback_refs[asset_id]=callback_ref
    
    def get_asset_callback_ref(self, asset_id): 
        '''
        Return callback reference for this asset_id
        '''
        if asset_id not in self.testruns:
            raise KeyError("No such asset listed")
        elif asset_id not in self.callback_refs:
            raise ValueError("No callback reference added for this asset ID")
        else:
            return self.callback_refs[asset_id]
            
    def get_testrun(self, TUID):
        for testruns_list in self.testruns.values():
            for testrun in testruns_list:
                if TUID == testrun.TUID:
                    return testrun
        
        raise KeyError("No such testrun listed") 
    
    def asset_used(self, asset_id):
        '''
        Check if asset_id is actively used by any testruns or not. True it is used and False if not used.
        '''
        for testruns_list in self.testruns.values():
            for testrun in testruns_list:
                if (testrun.asset_id == asset_id) and (testrun.state == "OPEN"): # uses this asset set and is open
                    return True 
        
        return False
    
    def __iter__(self): 
        '''
        Iter method to return iterator and also reset all iteration related attributes
        '''
        self.list_of_testruns=[] # get a list of all testruns
        for testruns_list in self.testruns.values():
            self.list_of_testruns=self.list_of_testruns+list(testruns_list)
        
        self.iter_index=0 # reset  list index
        self.iter_stop=len(self.list_of_testruns) # set stopping value
        return self
    
    def __next__(self):
        '''
        Next method to iterate over all the registered testruns
        '''
        if self.iter_index >= self.iter_stop:
            raise StopIteration
        else:
            iter_val=self.list_of_testruns[self.iter_index]
            self.iter_index+=1 # increment index
            return iter_val

class testruns(object):
    
    def __init__(self, data_collector, sql): # user can specify the starting value for order_id (incase we are going from backtest to forward test)
        self.data_collector=data_collector
        self.sql=sql
        self.sql_input, self.sql_output=self.sql.get_io()
        self.testruns_dict={}
        self.testrun_manager=testrunManager()
    
    # def is_name_used(self, name): # check that we do not have a testrun/strategy with this name in the dictionary
    #     for testruns_list in self.testruns_dict.values():
    #         # if name in strat_names_list:
    #         #     return False
    #         for testrun in testruns_list:
    #             if name == testrun.name:
    #                 return True
    #     return False
    
    def exception_handler(self, e, TUID):
        testrun=self.testrun_manager.get_testrun(TUID)
        testrun.close_testrun() # close down testrun
        self.sql.close_testrun(testrun) # close testrun in database and also close streamer
        # if not self.is_asset_used(testrun.asset_id): # is asset not used by any other testruns
        #     self.data_collector.del_symbol(testrun.asset_id)
        # self.del_testrun(TUID) # remove garbage values that might have been created
        self.remove_asset(testrun)
        self.del_testrun(TUID)
        testrun.exception_callback(e, TUID) # call the callback provided by the user (controller.py)
    
    def ticker_update_callback(self, data):
        pack=packet(operations.save_ticker_data, data[0], data[1])
        self.sql_input.put(pack)
    
    def remove_asset(self, testrun):
        '''
        Check if asset used by any testruns and if not then remove its callback and the asset from monitor list in tvDatafeedRealtime
        '''
        asset_id=testrun.asset_id
        if not self.testrun_manager.asset_used(asset_id):
            self.data_collector.del_callback(self.testrun_manager.get_asset_callback_ref(asset_id))
            self.data_collector.del_symbol(asset_id)
    
    def new_testrun(self, testrun_name, strategy, symbol, exchange, interval, account_size, exception_callback):  
        asset_id=self.data_collector.add_symbol(symbol, exchange, interval) # get ID for this asset set - it might already exists in data_collector
        callback_id=self.data_collector.add_callback(asset_id, self.ticker_update_callback) # add a callback function to stream ticker data into SQL database
        new_testrun=testrun(testrun_name, dt.now().strftime("%Y-%m-%d %H:%M:%S"), \
                            symbol, exchange, str(interval), asset_id, account_size, exception_callback) # opposite operation is datetime_obj=dt.strptime(start_dt_str,"%d-%m-%y %H:%M")
        new_testrun=self.sql.add_testrun(new_testrun) # add testrun into SQL database and assign TUID for testrun
        TUID=new_testrun.get_TUID()
        strat_ref=strategy_runner(self.data_collector, self.sql_input, TUID, asset_id, strategy, self.exception_handler) # SOMEHOW HAVE TO ENTER THE SQL_INPUT FOR STRATEGY INSTANCE
        new_testrun.add_strat_ref(strat_ref)
        self.testrun_manager.add_testrun(new_testrun)
        self.testrun_manager.set_asset_callback_ref(asset_id, callback_id)
        # if asset_id in self.testruns_dict.keys(): # if already existing then just append testrun reference
        #     self.testruns_dict[asset_id].append(new_testrun)
        # else: # need to create a new key-value pair and add it into new list
        #     self.testruns_dict[asset_id]=[new_testrun]
        strat_ref.start() # start the strategy in that testrun
        # else:
        #     raise ValueError("Strategy with this name already running") 
        
        return TUID
    
    def close_testrun(self, TUID):
        testrun=self.testrun_manager.get_testrun(TUID) # get testrun object based on TUID
        if testrun.state == "OPEN": # check that it hasn't already been closed (by exception handler)
            testrun.close_testrun() # change the testrun status
            self.sql.close_testrun(testrun) # close testrun in database and also close streamer
            testrun.get_strat_ref().stop() # stop the strategyRunner instance for this strategy
            self.remove_asset(testrun) # check and remove callback if this asset not used anymore
        # if not self.is_asset_used(testrun.asset_id): # is asset not used by any other testruns
        #     self.data_collector.del_symbol(testrun.asset_id)
    
    def close_all_testruns(self):
        '''
        Close all open testruns
        '''
        for testrun in self.testrun_manager:
            if testrun.state == "OPEN": # check that it hasn't already been closed (by exception handler)
                testrun.close_testrun() # change the testrun status
                self.sql.close_testrun(testrun) # close testrun in database and also close streamer
                testrun.get_strat_ref().stop() # stop the strategyRunner instance for this strategy
            
            # if not self.is_asset_used(testrun.asset_id): # is asset not used by any other testruns
            #     self.data_collector.del_symbol(testrun.asset_id)
    
    def del_testrun(self, TUID):
        '''
        Delete the testrun from testruns dictionary and remove from SQL database
        '''
        self.testrun_manager.del_testrun(TUID)
        # asset_id=testrun.asset_id
        # self.testruns_dict[asset_id].remove(testrun) # remove testrun from the list
        # if not self.testruns_dict[asset_id]: # no more testruns for this asset_id remove asset_id group from dictionary
        #     del self.testruns_dict[asset_id]
        
        self.sql.del_testrun(TUID)
            
    # def get_testrun(self, TUID):
    #     for testruns_list in self.testruns_dict.values():
    #         for testrun in testruns_list:
    #             if TUID == testrun.TUID:
    #                 return testrun
    #
    #     return None # if no such testrun exists 
    #
    # def is_asset_used(self, asset_id):
    #     '''
    #     Check if this asset set is used by any testruns
    #     '''
    #     for testruns_list in self.testruns_dict.values():
    #         for testrun in testruns_list:
    #             if (testrun.asset_id == asset_id) and (testrun.state == "OPEN"): # uses this asset set and is open
    #                 return True 
    #
    #     return False
    
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
        self.close_datetime=dt.now().strftime("%Y-%m-%d %H:%M:%S")
        #self.close_callback(self.asset_id, self)
    
    def get_sql_params(self):
        if self.state == "OPEN":
            return (self.name, "NEW", self.start_datetime, self.close_datetime, self.symbol, \
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
