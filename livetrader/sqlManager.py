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

import sqlite3, threading, queue
from datetime import datetime as dt
from enum import Enum
import pandas as pd

class operations(Enum):
    open_order=1
    close_order=2
    save_ticker_data=3
        
class packet(object):
    
    def __init__(self, op=None, ident=None, data=None):
        self.operation=op # use operations class instance to define which operation to perform
        self.ident=ident # either TUID (order packet) or asset_id (ticker data packet)
        self.data=data # order or ticker data
    
    def get_id(self):
        return self.ident
    
    def set_id(self, ident):
        self.ident=ident
    
    def get_operation(self):
        return self.operation
    
    def set_operation(self, op):
        self.operation=op
        
    def get_data(self):
        return self.data
    
    def add_data(self,data):
        self.data=data

class sqlDatabase(object):
    
    def __init__(self, path): # need to specify full path (with database name) to where database should be - if it isn't there then it will be created
        self.db_con=sqlite3.connect(path, check_same_thread=False) # application must make sure that writing to DB is serialized
        self.db_cursor=self.db_con.cursor()
        # check if we have "testruns" table created in this database already 
        self.db_cursor.execute('SELECT name from sqlite_master WHERE type = "table" AND name = "testruns"')
        # if not then create both tables "testruns" and "orders"
        if not self.db_cursor.fetchall(): # if list if empty then tables do not exist
            self._query_create_tables()
    
    def close(self):
        self.db_con.commit() # commit whatever changes wqe might have unsaved
        self.db_con.close() # close the connection
        
    def _query_create_tables(self):
        self.db_cursor.execute("CREATE TABLE testruns (TUID INTEGER PRIMARY KEY, \
                                                        name TEXT NOT NULL, \
                                                        state TEXT NOT NULL, \
                                                        start_datetime TEXT NOT NULL, \
                                                        close_datetime TEXT, \
                                                        symbol TEXT NOT NULL, \
                                                        exchange TEXT NOT NULL, \
                                                        interval TEXT NOT NULL, \
                                                        starting_account REAL, \
                                                        closing_account REAL)")
        
        self.db_cursor.execute("CREATE TABLE orders (order_id INTEGER NOT NULL, \
                                                    TUID INTEGER REFERENCES testruns, \
                                                    state TEXT NOT NULL, \
                                                    open_datetime TEXT NOT NULL, \
                                                    close_datetime TEXT, \
                                                    order_type TEXT NOT NULL, \
                                                    entry_price REAL NOT NULL, \
                                                    close_price REAL, \
                                                    position_size REAL NOT NULL, \
                                                    stop_loss_price REAL NOT NULL, \
                                                    take_profit_price REAL NOT NULL, \
                                                    open_account_size REAL NOT NULL, \
                                                    close_account_size REAL, \
                                                    PRIMARY KEY(TUID, order_id))")
        
        self.db_cursor.execute("CREATE TABLE ticker_data (ID INTEGER PRIMARY KEY, \
                                                        asset_id INTEGER, \
                                                        datetime TEXT NOT NULL, \
                                                        symbol TEXT NOT NULL, \
                                                        open REAL NOT NULL, \
                                                        high REAL NOT NULL, \
                                                        low REAL NOT NULL, \
                                                        close REAL NOT NULL,\
                                                        volume REAL NOT NULL)")
        
        self.db_con.commit()
        
    def query_insert_testrun(self, testrun_data): # this method returns TUID (row_id) of the newly added testrun
        # create a new entry in testruns table
        self.db_cursor.execute("INSERT INTO testruns VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)", testrun_data) # testrun_data must be a tuple
        self.db_con.commit()
        # get the auto-incremented TUID value using state field
        self.db_cursor.execute("SELECT * FROM testruns WHERE state = ?", ("NEW",))
        tuid=self.db_cursor.fetchall()[0][0] # fetchall returns a list of tuples; we select the first element from the first tuple
        # change the state field to "OPEN"
        self.db_cursor.execute("UPDATE testruns SET state = (?) WHERE TUID = (?)",("OPEN",tuid))
        self.db_con.commit()
        
        return tuid
    
    def query_insert_ticker(self, asset_id, ticker_data):
        '''
        Save ticker data into SQL ticker_data table. Input must be a Pandas DataFrame created by tvDatafeed.
        '''
        for index, row in ticker_data.iterrows(): # iterate over all the rows in DataFrame; OPPOSITE operation is pd.Timestamp(dt.strptime(t_string,"%Y-%m-%d %H:%M:%S"))
            self.db_cursor.execute("INSERT INTO ticker_data VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", (asset_id, \
                                                                                                  str(index), \
                                                                                                  row.symbol, \
                                                                                                  row.open, \
                                                                                                  row.high, \
                                                                                                  row.low, \
                                                                                                  row.close, \
                                                                                                  row.volume))
        
        self.db_con.commit()
        
    def query_insert_order(self, order_data):
        self.db_cursor.execute("INSERT INTO orders VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", order_data) # order_data must be a tuple 
        self.db_con.commit()
    
    def query_update_testrun(self, testrun_data):
        # get the closing account size from the last closed order
        self.db_cursor.execute("SELECT close_account_size FROM orders WHERE TUID = (?) AND state = 'CLOSED' ORDER BY order_id DESC LIMIT 1", (testrun_data[-1],)) 
        closing_account_size=self.db_cursor.fetchall() # returns a list of tuples 
        if len(closing_account_size) == 0: # in case there was no closed orders (testrun closed right after it opened) the closing account will be NULL; TODO: account size should be then open accoutn size instead
            testrun_data=("NULL",) + testrun_data # create a new tuple where first element is the closing_account size
        else: # create a new tuple which includes the account size of the last closed order
            testrun_data=closing_account_size[0] + testrun_data
        self.db_cursor.execute("UPDATE testruns SET closing_account = (?), state = (?), close_datetime = (?) WHERE TUID = (?)",testrun_data)
        self.db_con.commit()
    
    def query_update_order(self, order_data): # order_data must specify TUID and order_id pair to identify the correct row in orders table
        self.db_cursor.execute("UPDATE orders SET state = (?), close_datetime = (?), close_price = (?), close_account_size = (?) WHERE TUID = (?) AND order_id = (?)",order_data)
        self.db_con.commit()
        
    def query_read_orders(self, TUID):
        self.db_cursor.execute("SELECT * FROM orders WHERE TUID = ?",(TUID,))
        return self.db_cursor.fetchall()
    
    def query_read_testruns(self):
        self.db_cursor.execute("SELECT * FROM testruns")
        return self.db_cursor.fetchall()
    
    def query_read_ticker_data(self, asset_id):
        '''
        Retrieve all ticker data from SQL based on asset_id. Ticker data will be provided in Pandas DataFrame
        '''
        ticker_data=pd.DataFrame() # create empty dataframe where we will put data
        ticker_data.index.name="datetime"
        
        self.db_cursor.execute("SELECT * FROM ticker_data WHERE asset_id = ?",(asset_id,)) # retrieve all ticker data for this asset_id
        data_tuples_list=self.db_cursor.fetchall()
        
        for data_tuple in data_tuples_list:
            ticker_data=pd.concat([ticker_data,pd.DataFrame(data={"symbol" : data_tuple[3], \
                                                                    "open" : data_tuple[4], \
                                                                    "high" : data_tuple[5], \
                                                                    "low" : data_tuple[6], \
                                                                    "close" : data_tuple[7], \
                                                                    "volume" : data_tuple[8]}, \
                                                                    index=[data_tuple[2]])]) # index/datetime column
                
        return ticker_data
        
    def query_delete_testrun(self, TUID):
        self.db_cursor.execute("DELETE FROM testruns WHERE TUID = (?)", (TUID,))
        self.db_con.commit()
        
    def query_delete_ticker_data(self, asset_id):
        self.db_cursor.execute("DELETE FROM ticker_data WHERE asset_id = (?)", (asset_id,))
        self.db_con.commit()
    
    def query_delete_orders(self, TUID):
        self.db_cursor.execute("DELETE FROM orders WHERE TUID = (?)", (TUID,))
        self.db_con.commit()
    
class sqlManager(threading.Thread):

    def __init__(self, database_path=None):
        '''
        Constructor
        '''
        if database_path is None:
            raise ValueError("No path for SQL database provided")
        self.database=sqlDatabase(database_path) # user should be able to provide the path for this ???
        threading.Thread.__init__(self)
        self.run_mode=threading.Event()
        self.run_mode.set() # until this event is cleared we will run this thread
        self.active_listen=[None,None] # must be a list of Nones because we are checking fro both TUID and asset_id
        self.lock=threading.Lock()
        self.input_queue=queue.Queue() # all strategies and data collector will place their data onto this queue for manager to process
        self.output_queue=queue.Queue() # this will go to GUI for sending data streams
        
    def get_io(self):
        return [self.input_queue, self.output_queue] 
    
    def run(self):
        while self.run_mode.isSet():
            packet=self.input_queue.get()
            self.get_lock()
            self.process_block(packet)
            self.drop_lock()
        
        self.database.close() # close the database connection
    
    def process_block(self, packet): # this method reads the operation type and based on that performs it; valid operations: create_testrun, close_testrun, open_order, close_order
        #sender=packet.get_id() # get senders ID                 
        op=packet.get_operation() # get the oepration type
        data=packet.get_data()
        sender=packet.get_id()
        
        if op is operations.open_order:
            sql_params=data.get_sql_params()
            self.database.query_insert_order(sql_params) 
        elif op is operations.close_order:
            sql_params=data.get_sql_params()
            self.database.query_update_order(sql_params)
        elif op is operations.save_ticker_data:
            # TICKER DATA IS A PANDAS OBJECT WHICH CAN CONTAIN 1 OR MANY DATA POINTS - NEED TO WRITE THEM INTO SQL ONE-BY-ONE
            self.database.query_insert_ticker(sender, data)
        
        if sender in self.active_listen: # if the packet was from Strategy that we are actively monitoring then pass that along to the GUI
            self.output_queue.put(packet)
    
    def get_lock(self, timeout=-1):
        self.lock.acquire(timeout=timeout)
    
    def drop_lock(self):
        self.lock.release()
    
    def add_testrun(self, testrun):
        sql_params=testrun.get_sql_params()
        self.get_lock() # as thread might be running at the same time then lock the resource before continuing
        TUID=self.database.query_insert_testrun(sql_params)
        # self.active_listen=TUID # save the TUID for which testrun we are actively forwarding (streaming) order (and in future ticker) data
        self.drop_lock()
        testrun.set_TUID(TUID)
        return testrun
    
    def close_testrun(self, testrun):
        sql_params=testrun.get_sql_params()
        TUID=testrun.get_TUID()
        self.get_lock()
        self.database.query_update_testrun(sql_params)
        if TUID in self.active_listen: # if we were forwarding data for this testrun then stop
            self.active_listen=[None,None]
        self.drop_lock()
    
    # write this as a direct method called by controller
    def read_testruns(self): # this function returns all the orders which are newly added
        '''
        Return a list of tuples. Each tuple is a testrun (entry) that is registered in SQL database.
        '''
        self.get_lock()
        testruns=self.database.query_read_testruns()
        self.drop_lock()
        
        return testruns
    
    # write this as a direct method called by controller
    def read_orders(self, TUID): # this function returns all the orders which are newly added
        self.get_lock()
        orders=self.database.query_read_orders(TUID)
        self.drop_lock()
        return orders
    
    def read_ticker_data(self, asset_id):
        self.get_lock()
        ticker_data=self.database.query_read_ticker_data(asset_id)
        self.drop_lock()
        return ticker_data
        
    # write this as a direct method called by controller
    def set_streamer(self, TUID, asset_aid):
        self.get_lock() # as thread might be running at the same time then lock the resource before continuing
        self.active_listen=[TUID, asset_aid.get_ids()] # save the TUID for which testrun we are actively forwarding (streaming) order (and in future ticker) data
        self.drop_lock()
    
    def del_testrun(self, TUID):
        self.get_lock()
        self.database.query_delete_orders(TUID)
        self.database.query_delete_testrun(TUID)
        self.drop_lock()
    
    def del_ticker_data(self, asset_id):
        self.get_lock()
        self.database.query_delete_ticker_data(asset_id)
        self.drop_lock()
    
    def stop(self):
        self.run_mode.clear() # clear the flag - this will stop running the main while loop  