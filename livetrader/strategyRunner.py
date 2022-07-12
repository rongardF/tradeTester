'''
'''

import threading
import backtrader as bt
from backtrader.feeds.tvLiveDatafeed import tvLiveDatafeed as tld

class strategyRunner(threading.Thread):

    def __init__(self, data_collector, sql_input, TUID, asset_aid, strategy, except_hand_callback):
        # just save references which will be used when thread started - avoid raising any exception in init stage
        self.data_collector=data_collector
        self.sql_input=sql_input
        self.TUID=TUID
        self.strategy=strategy
        self.asset_aid=asset_aid
        self.live_feeds=[]
        self.callback_func=except_hand_callback
        threading.Thread.__init__(self)
    
    def run(self):
        try: # try executing the strategy - we might get raised exception (if user entered something wrong in strategy)
            for asset_id in self.asset_aid:
                self.live_feeds.append(tld(self.data_collector, asset_id)) # this feed will register for asset set (symbol, exchange, interval) specified with asset_id
            self.cerebro = bt.Cerebro()
            self.cerebro.addstrategy(self.strategy, sql_input=self.sql_input, TUID=self.TUID)
            for live_feed in self.live_feeds:
                self.cerebro.adddata(live_feed)
            self.cerebro.run()
        except Exception as e: # notify the caller about this strategy thread failing with exception e and close
            self.live_feed.remove_callback()
            self.callback_func(e, self.TUID)
        
    def stop(self):
        for live_feed in self.live_feeds:
            live_feed.remove_callback() # first remove callback from data_collector - then we can be sure that nothing else is calling receive_data() method
            live_feed.receive_data("EXIT") # send a signal to the feed that data streaming has ended (cerebro will finish)
        