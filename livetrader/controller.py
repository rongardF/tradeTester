###############################################################################
#
# Copyright (C) 2022-2023 Ron Freimann
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import threading, traceback

from datetime import datetime as dt
from tvDatafeed import Interval
from tvDatafeed import TvDatafeedLive
from livetrader.sql_manager import SqlManager
from livetrader.testrun import Testrun
from livetrader.strategy import Strategy
from backtrader import strategy

class asset(object):
    '''
    Symbol, exchange, intervals group 
    
    Holds symbol, exchange and list of Interval objects
    which together allow to define some number of Seis
    objects with various intervals, but same symbol and exchange
    values.
    
    The instance of this object is False until it has been validated
    with is_valid method which returns True. If that method returns
    false the invalid_pairs attribute will contain symbol-exchange 
    pairs which are not valid
    '''
    def __init__(self, symbol=None, exchange=None, intervals=[]): # intervals must be a list of Interval objects
        self.symbol=symbol
        self.exchange=exchange
        self.intervals=intervals
        self.valid=False
        self.invalid_pairs=[]
    
    def __bool__(self):
        return self.valid
    
    def __len__(self):
        return len(self.intervals)
    
    def __iter__(self): 
        self.intervals_iter=iter(self.intervals)
        return self
    
    def __next__(self):
        interval=next(self.intervals_iter)
        return self.symbol, self.exchange, interval
    
class Controller():
    '''
    classdocs
    '''

    def __init__(self, sql_path=None):
        '''
        Constructor
        '''
        self.tv_datafeed_live=TvDatafeedLive() 
        self.sql=SqlManager(sql_path) 
        self.sql.start()
        self.testruns={}
    
    def ranking(self): # TODO: currently just return unordered list of testruns, but in future this method should accept metrics names that should be used for ordering
        '''
        Return a list of all testruns in ranked order
        '''
        raise NotImplementedError
    
    def graph(self, tuid):
        '''
        Plot the testrun with all data collected so far
        '''
        raise NotImplementedError
    
    def info(self, tuid):
        '''
        Return info about testrun from testruns table
        '''
        raise NotImplementedError
    
    def orders(self, tuid):
        '''
        Return all orders for this testrun
        '''
        raise NotImplementedError
        
    def is_valid(self, asset):
        '''
        Check that provided symbol-exchange pairs are valid
        
        If method returns False the invalid symbol-exchange pairs
        are given in the invalid_pairs attribute of the asset
        
        Parameters
        ----------
        asset : asset
            Asset to be checked
            
        Returns
        -------
        boolean
            True if valid, False otherwise
        '''
        for symbol, exchange, _ in asset:
            if not self.tdl.search_symbol(symbol, exchange): # if empty list is returned then invalid
                asset.invalid_pairs.append(f"{symbol}:{exchange}")
        
        # if no invalid pairs then all valid
        if not asset.invalid_pairs:
            asset.valid=True
            
        return asset.valid 
    
    def _collect_price_data(self, seis, package):
        package.livetrader_data_id=seis.livetrader_data_id
        self.sql.put(package)
    
    def _exception_handler(self, e, tuid): # TODO: add information about thrown exception into SQL database as well
        '''
        Handle exceptions that might have been thrown in any of the testruns
        '''
        print("Exception from "+str(tuid))
        traceback.print_exception(e)
    
    def new_testrun(self, name, input_strategy, asset, settings): # account size does not actually matter if we want to only see if strat is net positive/negative, but it has to be big enough to consider strategies specifics
        '''
        Start a new testrun with provided strategy
        '''
        # check the asset and strategy
        if not self.is_valid(asset): # not valid
            print_statement=""
            for pair in asset.invalid_pairs: print_statement+f"\n{pair}"
            raise ValueError(f"Provided symbol-exchange pairs are not valid: {print_statement}")
        else:
            strategy=Strategy(input_strategy, len(asset))
            if not strategy.validate(): # validate strategy, if returns False
                traceback.print_exception(ValueError(f"Strategy {input_strategy.__name__} threw and exception:\n"))
                raise strategy.exception
            
        seises=[]
        for symbol, exchange, interval in asset:
            seis=self.tv_datafeed_live.new_seis(symbol, exchange, interval) 
            seis.livetrader_data_id=self.sql.add_data(seis) # create new attribute in Seis which helps to map to specific data in datas table
            seis.new_consumer(self._collect_price_data) # consumer that sends price action data to SQL       
            seises.append(seis)
            
        tuid=self.sql.add_testrun(name, strategy, seises, settings.account_size, settings.broker_comm) # add testrun into SQL database and get TUID; TODO: SQLite should also have a callback to error_handled in case there is any exception thrown related to some testrun
        testrun=Testrun(tuid, seises, self.sql, strategy.strategy, self._exception_handler) 
        testrun.start() # start the strategy in that testrun
        
        self.testruns[(name, tuid)]=testrun
    
    def stop_testrun(self, tuid):
        '''
        Stop strategy from running
        '''
        if tuid in self.testruns: # check first that such a testrun exists
            self.testruns[tuid].close() 
        else:
            raise ValueError("No testrun with such TUID value")
    
    def stop_all_testruns(self):
        '''
        Stop all strategies from running - this is called before closing down tradeTester application
        '''
        for testrun in self.testruns:
            testrun.close()
