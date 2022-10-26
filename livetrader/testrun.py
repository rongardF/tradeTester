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

import threading
import backtrader as bt
from backtrader.feeds.tvLiveDatafeed import tvLiveDatafeed as tld
from livetrader.sql_observer import SqlObserver

class Testrun(threading.Thread):

    def __init__(self, tuid, seises, sql, strategy, except_hand_callback):
        # just save references which will be used when thread started - avoid raising any exception in init stage
        self.sql=sql
        self.seises=seises
        self.tuid=tuid
        self.strategy=strategy
        self.live_feeds=[]
        self.callback_func=except_hand_callback
        super().__init__()
    
    def run(self):
        try: # try executing the strategy - we might get exception (if strategy has a fault)
            self.cerebro = bt.Cerebro(stdstats=False) # disable default observers
            self.cerebro.addobserver(SqlObserver, sql=self.sql, tuid=self.tuid) # add observer which reports data to SQL Manager, SQL ref and TUID number
            self.cerebro.addstrategy(self.strategy)
            for seis in self.seises:
                live_feed=tld(seis) # create live feeds with each seis
                self.cerebro.add_data(live_feed)
                self.live_feeds.append(live_feed)
            self.cerebro.run(runonce=False) # force cerebro to perform calculations in next() method
        except Exception as e: # notify the caller about this strategy thread failing with exception e and close
            self.stop()
            self.callback_func(e, self.tuid)
        
    def stop(self):
        for live_feed in self.live_feeds:
            live_feed.remove_callback() # kill the consumer thread producing new data
            live_feed.receive_data(None) # send a signal to the feed that data streaming has ended (cerebro will finish) - not needed in exception case, but in normal stop() call it is needed
        
        # stop and remove seises which are not used by any other testrun
        for seis in self.seises:
            if seis.consumed_by() > 1: # TODO: implement this method in TvDatafeedLive; 1 consumer will be price action writer
                seis.del_seis()