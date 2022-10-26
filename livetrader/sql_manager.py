'''
Created on 4. okt 2022

@author: User
'''
import sqlite3, os, sys, queue, threading, datetime
from livetrader import ObserverPackage
from pandas import DataFrame
from livetrader.sql_statements import sql_tables_statements, \
                                        sql_insert_testrun_statement, \
                                        sql_insert_data, \
                                        sql_insert_testrun_datas, \
                                        sql_insert_module, \
                                        sql_select_data, \
                                        sql_select_module_hash, \
                                        sql_insert_bar

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
        
        if os.path.isfile(self.path := os.path.join(path, "tradeTester_DB.db")): # create absolute path with DB file name and check it doesn't exists already
            raise ValueError("Provided directory already contains tradeTester database")
         
        # create database and connect
        self.connection=sqlite3.connect(os.path.join(path, "tradeTester_DB.db"), check_same_thread=False) # DB can be accessed from multiple threads, user must make access serialized
        self.cursor=self.connection.cursor()
        
        # create all the tables in DB
        for statement in sql_tables_statements:
            self.cursor.execute(statement)
        self.connection.commit()
        
        # create a FIFO for input data
        self.in_fifo=queue.Queue()
        
        # cache tables to avoid reading from DB everytime
        self.indicators={"indicator_name" : indicator_id}
        self.lines={(tuid, indicator_name, line_name) : line_id}
        
        # initialize threading stuff
        super().__init__()
        self.lock=self.Lock() # used to synchronize access between buffer writes and direct method calls
        
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
    
    def add_data(self, seis):
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
    
    def _add_indicator(self):
        '''
        Add new indicator definition in indicators table
        '''
        raise NotImplementedError
    
    def _add_testrun_indicator(self):
        '''
        Add instance of indicator to particular testrun
        '''
        raise NotImplementedError
    
    def _insert_testrun_indicator_values(self):
        '''
        Insert indicator lines values into lines_values table
        '''
        raise NotImplementedError
    
    def add_testrun(self, name, strategy, seises, account_size, broker_comm):
        '''
        Create a new testrun entry in database
        '''
        # add strategy module into modules table
        with open(strategy.file, 'rb') as file:
            blob=file.read()
        blob_hash=hash(blob)
        # check if such file already exists
        sel_result=self.cursor.execute(sql_select_module_hash, (blob_hash,)).fetchone()
        if sel_result is None: # no such strategy file, insert into table
            self.cursor.execute(sql_insert_module, (0, blob_hash, blob)) # type 0 means strategy file type 1 means indicator file
            self.connection.commit()
            module_id=self.cursor.lastrowid
        else: # file already exists get module_id
            module_id=sel_result[0]
            
        # add indicator modules(s) into modules and indicators tables
        # TODO: there must be some function defined which parses strategy file and extracts all indicators used and runs initial test on strategy and imports the strategy as class
            
        # insert testrun entry into testruns table
        start_dt=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(sql_insert_testrun_statement, (name, start_dt, account_size, broker_comm, module_id))
        self.connection.commit()
        tuid=self.cursor.lastrowid
           
        # insert Seises used in testrun into datas and testrun_datas_list tables
        for seis in seises:
            # get the data_id
            sel_result=self.cursor.execute(sql_select_data, (seis.symbol, seis.exchange, seis.interval.value)).fetchone()
            data_id=sel_result[0]
                
            self.cursor.execute(sql_insert_testrun_datas, (tuid, data_id))
            self.connection.commit()
            
    def close_testrun(self):
        '''
        Close the testrun and update testrun entry in testruns table
        '''
        raise NotImplementedError
    
    def add_module_file(self):
        '''
        Add a new module file into modules table
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
            
            