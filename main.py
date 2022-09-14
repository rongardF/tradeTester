# '''
# '''
# import threading
# import backtrader as bt
# import traceback
# import time
# from datetime import datetime as dt
# from tvDatafeed import Interval
#
# from livetrader.orders import ordersManager
# from livetrader.sqlManager import operations, packet
# from livetrader.controller import controller, asset_set
#
# from backtrader.feeds.tvLiveDatafeed import tvLiveDatafeed as tld
# from tvDatafeed import Interval
# from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
# from tvDatafeed import TvDatafeed
# import backtrader.feeds as btfeeds
#
# def terminal(queue):
#     while True:
#         pack=queue.get()
#         # print out info from data
#         order=pack.get_data()
#         if pack.get_operation() != operations.save_ticker_data:
#             print("Order "+order.state+" with entry price "+str(order.entry_price)+" and close price "+str(order.close_price))
#
# class testStrategy(bt.Strategy):
#
#     def __init__(self):
#         pass
#
#     def next(self):
#         print("Close price of 3 minute interval: "+str(self.datas[0].lines.close[0]))
#         print("Close price of 5 minutes interval: "+str(self.datas[1].lines.close[0]))
#
# # this strategy opens and closes orders in sequence to test the tradeTester
# class MyStrategy(bt.Strategy):
#     params = (
#         ("sql_input", None),
#         ("TUID", None),
#         )
#
#     def __init__(self):
#         self.orders=ordersManager(self.p.TUID)
#         self.order=None
#
#     def next(self):
#         if self.order: # if order already created then close it
#             #raise ValueError("TEST")
#             print("order closed")
#             self.order.close_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), self.data.close[0], 10000.0)
#             pack=packet(operations.close_order, self.order.TUID, self.order)
#             self.p.sql_input.put(pack)
#             self.order=None
#         else: # if not then open new order
#             print("order created, first bar is "+str(self.datas[0].lines.close[0])+" and second bar is "+str(self.datas[1].lines.close[0]))
#             self.order=self.orders.new_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
#             pack=packet(operations.open_order, self.order.TUID, self.order)
#             self.p.sql_input.put(pack)
#
# class MyStrategy1(bt.Strategy):
#     params = (
#         ("sql_input", None),
#         ("TUID", None),
#         )
#
#     def __init__(self):
#         self.orders=ordersManager(self.p.TUID)
#         self.order=None
#
#     def next(self):
#         if self.order: # if order already created then close it
#
#             self.order.close_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), self.data.close[0], 10000.0)
#             pack=packet(operations.close_order, self.order.TUID, self.order)
#             self.p.sql_input.put(pack)
#             self.order=None
#         else: # if not then open new order
#             self.order=self.orders.new_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
#             pack=packet(operations.open_order, self.order.TUID, self.order)
#             self.p.sql_input.put(pack)
#
# if __name__ == "__main__":
#     contr=controller(r"C:\Users\User\Documents\Projektid\Python\tradeTester\development_materials\test_db.db")
#     #contr.start()
#     asset1=asset_set("ETHUSDT", "KUCOIN", [Interval.in_3_minute, Interval.in_5_minute])
#     asset2=asset_set("ETHUSDT", "KUCOIN", [Interval.in_1_minute, Interval.in_3_minute])
#     tuid1=contr.start_testrun("myTest1", MyStrategy, asset1, 10000) # strategy name must be unique and orders for that testrun must be removed from DB before running
#     tuid2=contr.start_testrun("myTest2", MyStrategy, asset2, 10000)
#     # tuid3=contr.start_testrun("myTest", MyStrategy1, "ETHUSDT", "KUCOIN", "3 minutes", 10000)
#     contr.select_testrun(tuid2)
#     t=threading.Thread(target=terminal, args=(contr.sql_output,))
#     t.start()
#     # print("Thread started, waiting...")
#     # time.sleep(400)
#     # print("Printing out from TUID 1...")
#     # contr.select_testrun(tuid1)
#     # time.sleep(300)
#     # print("Printing testruns...")
#     # print(contr.get_testruns())
#     # print("Printing ticker data...")
#     # print(contr.get_ticker_data(tuid1))
#     # print("Printing order data...")
#     # print(contr.get_orders(tuid2))
#     # print("Stopping testrun 2...")
#     # contr.stop_testrun(tuid2)
#     time.sleep(180)
#     print("Stopping all testruns...")
#     contr.stop_all_testruns()
#     #
#     # datafeeds_list=[]
#     # data_collector=tdr(True)
#     #
#     # asset_id1=data_collector.add_symbol("ETHUSDT", "KUCOIN", Interval.in_3_minute)
#     # asset_id2=data_collector.add_symbol("ETHUSDT", "KUCOIN", Interval.in_5_minute)
#     #
#     # datafeeds_list.append(tld(data_collector, asset_id1))
#     # datafeeds_list.append(tld(data_collector, asset_id2))
#     #
#     # cerebro = bt.Cerebro()
#     # cerebro.addstrategy(testStrategy)
#     # for feed in datafeeds_list: # add all data feeds to cerebro, each needs to be added with separate call to adddata() method
#     #     cerebro.adddata(feed) 
#     # cerebro.run()

import time
from tvDatafeedRealtime import tvDatafeedRealtime
from tvDatafeed import Interval

def cb(data):
    print("Ticker set id "+str(data[0])+ " produced close price "+str(data[1].close))

collector=tvDatafeedRealtime()
asset_id=collector.add_symbol("ETHUSDT", "KUCOIN", Interval.in_1_minute)
callback_ref=collector.add_callback(asset_id, cb)

time.sleep(300)
print("deleting callback ref")
collector.del_callback(callback_ref)
time.sleep(20)
print("deleting symbol")
collector.del_symbol(asset_id)

