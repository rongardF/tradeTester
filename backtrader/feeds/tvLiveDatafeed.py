'''
CONTINUE:
Study how Cerebro works with differnt data sets and how to access those different data sets

Each live feed is a separate data object - for multiple assets(intervals) we need to create multiple separate live feeds and feed them into cerebro.
The live feed object itself should not change, but the startegyRunner should change to create separate livefeeds based on asset_ids
'''

import queue
from backtrader import date2num
from backtrader.feeds import DataBase

class tvLiveDatafeed(DataBase): # PARENT class is AbstractDataBase

    def __init__(self, tv_datafeed_realtime, asset_id):
        self.tdr=tv_datafeed_realtime
        self.callback_id=self.tdr.add_callback(asset_id, self.receive_data) # add callback method for this asset set; keep callback id so later we can remove it
        self.data_queue=queue.Queue() # queue where all the new data is put for the _load() method to process
        
    def start(self):
        super().start() 

    def receive_data(self, data): # this function is called by the tvDatafeedRealtime whenever the symbol we use in this datafeed has a new value
        self.data_queue.put(data[1]) # put new data in to queue and ignore the asset_id part
    
    def remove_callback(self):
        self.tdr.del_callback(self.callback_id)

    def _load(self):  # this is called inside the load() method in AbstractDataBase and will actually assign data to lines
        if not self.data_queue.empty(): # if there is new data in the queue
            data=self.data_queue.get() # get next available data bar
            if isinstance(data,str): # if string is received then that is "EXIT"
                return False # means user stopped this strategy
            
            # add new data together with its datetime into lines
            self.lines.datetime[0] = date2num(data.index[0])
            # Get the rest of the unpacked data
            self.lines.open[0] = data.open[0]
            self.lines.high[0] = data.high[0]
            self.lines.low[0] = data.low[0]
            self.lines.close[0] = data.close[0]
            self.lines.volume[0] = data.volume[0]
            self.lines.openinterest[0] = 0 # there is no such data in tvDatafeed so keep it zero
            
            return True
        else:
            return None

    def islive(self):
        '''Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated'''
        return True

    def stop(self):
        '''Stops and tells the store to stop'''
        super().stop() # calls PARENT class (AbstractDataBase) stop() method
