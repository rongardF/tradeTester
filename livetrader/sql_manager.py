'''
Created on 4. okt 2022

@author: User
'''
import sqlite3, os, sys, queue, threading, datetime, hashlib
from livetrader import ObserverPackage
from pandas import DataFrame
from livetrader.sql_statements import sql_tables_statements, \
                                        sql_insert_testrun_statement, \
                                        sql_insert_data, \
                                        sql_insert_testrun_datas, \
                                        sql_insert_module, \
                                        sql_insert_bar, \
                                        sql_insert_indicator, \
                                        sql_select_indicators_all, \
                                        sql_select_indicator_hashes, \
                                        sql_select_indicators, \
                                        sql_insert_sub_indicator, \
                                        sql_insert_testrun_indicator, \
                                        sql_insert_indicator_line, \
                                        sql_insert_plotlines_data, \
                                        sql_insert_testrun_indicators_plotinfo, \
                                        sql_insert_plothlines_lists, \
                                        sql_insert_plotyticks_lists, \
                                        sql_insert_plotyhlines_lists, \
                                        sql_select_modules, \
                                        sql_select_datas

class SqlManager(threading.Thread): # TODO: use SqlAlchemy in the future to make it database agnostic
    '''
    classdocs
    '''

    def __init__(self, path=None): # the user must specify absolute path to directory where DB will be placed
        '''
        Constructor
        '''
        # check path and directory for old DB
        if path is None: # TODO: make it so that if None provided then run SQLite in memory
            raise ValueError("No path for SQL database provided")
        
        if os.path.isfile(path := os.path.join(path, "tradeTester.db")): # create absolute path with DB file name and check it doesn't exists already
            raise ValueError("Provided directory already contains tradeTester database")
         
        # create database and connect
        self.connection=sqlite3.connect(path, check_same_thread=False) # DB can be accessed from multiple threads, user must make access serialized
        self.cursor=self.connection.cursor()
        
        # create all the tables in DB
        for statement in sql_tables_statements:
            self.cursor.execute(statement)
        self.connection.commit()
        
        # create a FIFO for input data
        self.in_fifo=queue.Queue()
        
        # cache table to avoid reading from DB
        self.indicator_line_ids={}
        
        # initialize threading stuff
        super().__init__()
        self.lock=threading.Lock() # used to synchronize access between buffer writes and direct method calls
        
    def __del__(self):
        self.connection.close() # close the DB connection
    
    def put(self, tuid, data):
        '''
        Put data into FIFO buffer to be written into database
        '''
        self.in_fifo.put((tuid, data))
    
    def get_data(self, data_id): # TODO: add some parameters which can define the period for which data is required; this is used when starting testrun with hist=True
        '''
        Return a DataFrame containing all bar values
        '''
        raise NotImplementedError
    
    def add_data(self, seis): # TODO: insert data as executemany to save time on commiting
        '''
        Create a new data entry in datas table
        '''
        self.cursor.execute(sql_insert_data, (seis.symbol, seis.exchange, seis.interval.value))
        self.connection.commit()
        data_id=self.cursor.lastrowid
        
        return data_id
    
    def _insert_data_values(self):
        '''
        Insert new data bar into bars table
        '''
        raise NotImplementedError
    
    def _create_blob(self, file):
        # Create a binary file and get hash of it
        with open(file, 'rb') as f:
            blob=f.read()
        h=hashlib.md5()
        h.update(blob)
        blob_hash=int.from_bytes(h.digest(), "big")
        
        return (blob, blob_hash)
    
    def _add_indicators(self, indicators):
        # Add indicators and indicator files into DB,
        # return a list of indicator name and ID pairs
        # for those indicators
        
        testrun_indicators=[] 
        strategy_indicators={}
        
        db_data=self.cursor.execute(sql_select_indicators).fetchall() # returns a list of tuples (blob_hash, indicator_name, indicator_id)
        db_indicators={}
        for indicator in db_data: 
            db_indicators[indicator[0]]=(indicator[1], indicator[2])
        
        # add indicator modules(s) into modules and indicators tables
        for indicator in indicators:
            # extract names and file
            parent_ind_name=indicator.parent
            ind_name=indicator.name
            ind_file=indicator.file
            # create a blob and a hash
            #ind_blob, ind_hash=self._create_blob(ind_file)
            ind_module_id, ind_hash=self._insert_module_file(ind_file)
            
            # check if file already exists in DB - if not then insert
            if ind_hash not in db_indicators.keys():
                self.cursor.execute(sql_insert_indicator, (ind_name, ind_module_id)) # insert new indicator into indicators table
                new_ind_id=self.cursor.lastrowid
                db_indicators[ind_hash]= (ind_name, new_ind_id)  # update the list of indicators in DB
                
            indicator_id=db_indicators[ind_hash][1]
            strategy_indicators.setdefault(ind_name, indicator_id) # keep record of all unique indicators with their id in this strategy/testrun
            
            if parent_ind_name is None: # this is top-level indicator (not sub-indicator)
                testrun_indicators.append((indicator_id, indicator)) # append to list of indicators used in strategy
            else: # sub-indicator, add a relationship to some parent indicator
                # get the parent indicators id; in DB there can be 
                # duplicates with this name, which is why we keep 
                # reference of indicators used only in this testrun 
                # cause in single strategy/testrun there can not 
                # be any duplicates
                parent_indicator_id=strategy_indicators[parent_ind_name]  
                self.cursor.execute(sql_insert_sub_indicator, (parent_indicator_id, indicator_id))
        
        self.connection.commit() # commit changes
        
        return testrun_indicators # used to link indicators with this particular testrun 
    
    def _add_testrun_indicators(self, tuid, datas, testrun_indicators):
        # Link particular indicators from indicators
        # table to some specific testrun. Returns a 
        # dictionary linking tuid, indicator ID and 
        # lines IDs 
        
        indicator_line_ids={tuid: {}}
        
        for pair in testrun_indicators:
            indicator_id, indicator=pair # unpack
            
            # new entry in testrun_indicators table
            self.cursor.execute(sql_insert_testrun_indicator, (indicator_id, tuid, indicator.name))
            testrun_indicator_id=self.cursor.lastrowid
            indicator_line_ids[tuid][indicator.name]={} # new sub-dict for this indicator
            
            for line_name, attributes in indicator.plotlines.items():
                # add lines into indicator_lines table
                self.cursor.execute(sql_insert_indicator_line, (testrun_indicator_id, line_name))
                line_id=self.cursor.lastrowid
                indicator_line_ids[tuid][indicator.name].update({line_name: line_id}) # add line id for this indicator
            
                # add plotlines info into plotlines_data table
                for attr_name, attr_value in attributes:
                    self.cursor.execute(sql_insert_plotlines_data, (line_id, attr_name, attr_value))
            
            # add plotinfo data into testrun_indicators_plotinfo table
            self.cursor.execute(sql_insert_testrun_indicators_plotinfo, (testrun_indicator_id, \
                                                                         indicator.plotinfo.plot, \
                                                                         indicator.plotinfo.subplot, \
                                                                         indicator.plotinfo.plotname, \
                                                                         indicator.plotinfo.plotabove, \
                                                                         indicator.plotinfo.plotlinelabels, \
                                                                         indicator.plotinfo.plotlinevalues, \
                                                                         indicator.plotinfo.plotvaluetags, \
                                                                         indicator.plotinfo.plotymargin, \
                                                                         datas[indicator.plotinfo.plotmaster_data_index])) # convert data feed index into data feed data id
            
            # add plothlines, plotyticks and plotyhlines lists into SQL DB
            for plothline_value in indicator.plotinfo.plothlines:
                self.cursor.execute(sql_insert_plothlines_lists, (testrun_indicator_id, plothline_value))
                
            for plotytick_value in indicator.plotinfo.plotyticks:
                self.cursor.execute(sql_insert_plotyticks_lists, (testrun_indicator_id, plotytick_value))
                
            for plotyhline_value in indicator.plotinfo.plotyhlines:
                self.cursor.execute(sql_insert_plotyhlines_lists, (testrun_indicator_id, plotyhline_value))
        
        self.connection.commit() # commit changes
        
        return indicator_line_ids
    
    def _insert_testrun_indicator_values(self):
        '''
        Insert indicator lines values into lines_values table
        '''
        raise NotImplementedError
    
    def _insert_module_file(self, file):
        # Check if already exists if not then insert
        # returns module_id for the table entry
        blob, blob_hash=self._create_blob(file) # create a binary file and get hash of it
        
        db_data=self.cursor.execute(sql_select_modules).fetchall()
        modules={}
        for row in db_data:
            modules[int(row[0])]=row[1] # hash is key and module_id is value
        
        # sel_result=self.cursor.execute(sql_select_module_hash, (blob_hash,)).fetchone()        
        if blob_hash not in modules.keys(): # no such file, insert new into table
            self.cursor.execute(sql_insert_module, (0, str(blob_hash), blob)) # type 0 means strategy file type 1 means indicator file; converting hash to str because number itself is too large for SQL table
            module_id=self.cursor.lastrowid
            self.connection.commit() # commit changes
        else: # file already exists get module_id
            module_id=modules[blob_hash]
            
        return module_id, blob_hash
    
    def _insert_testrun_datas(self, tuid, seises):
        # Get the data feeds IDs and link them with this testrun
        # in the testrun_datas_list table. Returns a list of data_id
        # values 
        datas=[] # will hold data feed data_id values for this testrun
        
        db_datas=self.cursor.execute(sql_select_datas).fetchall()
        db_datas_dict={}
        for data in db_datas:
            db_datas_dict[(data[1], data[2], data[3])]=data[0]
        
        # insert Seises used in testrun into datas and testrun_datas_list tables
        for seis in seises:
            # get the data_id from datas table 
            #sel_result=self.cursor.execute(sql_select_data, (seis.symbol, seis.exchange, seis.interval.value)).fetchone()
            data_id=db_datas_dict[(seis.symbol, seis.exchange, seis.interval.value)]
            datas.append(data_id)
                
            self.cursor.execute(sql_insert_testrun_datas, (tuid, data_id))
        
        self.connection.commit() # commit changes
        
        return datas
    
    def add_testrun(self, name, strategy, seises, account_size, broker_comm): 
        '''
        Create a new testrun entry in database
        '''
        if not self.lock.acquire(timeout=5):
            raise RuntimeError("Could not acquire lock") 
        
        module_id, _=self._insert_module_file(strategy.strategy_file)

        # insert testrun entry into testruns table
        start_dt=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(sql_insert_testrun_statement, (name, start_dt, account_size, broker_comm, module_id))
        tuid=self.cursor.lastrowid
        
        datas=self._insert_testrun_datas(tuid, seises)
        
        testrun_indicators=self._add_indicators(strategy.indicators)
        
        indicator_line_ids=self._add_testrun_indicators(tuid, datas, testrun_indicators)
        self.indicator_line_ids.update(indicator_line_ids)
        
        self.connection.commit() # commit all changes to DB
        
        self.lock.release()
        
        return tuid
            
    def close_testrun(self):
        '''
        Close the testrun and update testrun entry in testruns table
        '''
        raise NotImplementedError
    
    def insert_order(self):
        '''
        Insert new order into orders table
        '''
        raise NotImplementedError
    
    def update_order_status(self):
        '''
        Update the order status with new order notification
        '''
        raise NotImplementedError
    
    def run(self, package):
        # threading worktasks
        if type(package) == DataFrame: # price action data
            data_id=package.livetrader_data_id
            bars=[]
            # prepear SQL insertion parameters
            for index, row in package.iterrows():
                bars.append((data_id, str(index), row.close, row.open, row.high, row.low, row.volume))
            # insert data into table
            self.cursor.executemany(sql_insert_bar, bars)
            self.connection.commit()
        elif type(package) == ObserverPackage: # testrun observer data
            #TODO: unpack orders indicators and broker_data and write into SQL database
            pass
            