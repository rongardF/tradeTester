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
