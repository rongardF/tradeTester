# '''
# '''
# import threading
# import backtrader as bt
# import backtrader.indicators as btind
# # import traceback
# # import time
# from datetime import datetime as dt
# from tvDatafeed import TvDatafeed, Interval
# #
# # from livetrader.orders import ordersManager
# # from livetrader.sqlManager import operations, packet
# # from livetrader.controller import controller, asset_set
# #
# # from backtrader.feeds.tvLiveDatafeed import tvLiveDatafeed as tld
# # from tvDatafeed import Interval
# # from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
# # from tvDatafeed import TvDatafeed
# import backtrader.feeds as btfeeds
# import math, pandas, inspect, importlib

import traceback
from development_materials.testfile import MyStrategy
from livetrader import strategy
from livetrader import sql_manager
from tvDatafeed import TvDatafeedLive, Interval

s=strategy.Strategy(MyStrategy, 2)
s.validate()

sql=sql_manager.SqlManager(r"C:\Users\User\Documents\Projektid\Python\tradeTester\development_materials\database")

tdl=TvDatafeedLive() 
seis1=tdl.new_seis("ETHUSDT", "KUCOIN", Interval.in_1_minute) 
seis2=tdl.new_seis("ETHUSDT", "KUCOIN", Interval.in_3_minute)
sql.add_data(seis1)
sql.add_data(seis2)

seises=[seis1, seis2] 

tuid=sql.add_testrun("FIRST", s, seises, 10000.0, 0.0)

# #
# # def terminal(queue):
# #     while True:
# #         pack=queue.get()
# #         # print out info from data
# #         order=pack.get_data()
# #         if pack.get_operation() != operations.save_ticker_data:
# #             print("Order "+order.state+" with entry price "+str(order.entry_price)+" and close price "+str(order.close_price))
# #
# class testStrategy(bt.Strategy): 
#
#     def __init__(self):
#         pass
#
#     def next(self):
#         # print("Close price of 3 minute interval: "+str(self.datas[0].lines.close[0]))
#         # print("Close price of 5 minutes interval: "+str(self.datas[1].lines.close[0]))
#         pass
#
# class SimpleMovingAverage1(btind.Indicator):
#     lines = ('sma',)
#     params = (('period', 20),)
#
#     def __init__(self):
#         self.addminperiod(self.params.period)
#
#     def next(self):
#         datasum = math.fsum(self.data.get(size=self.p.period))
#         self.lines.sma[0] = datasum / self.p.period
#
# class DummyInd0(bt.Indicator):
#     lines = ('dummyline', 'previous', 'value')
#     params = (('value', 5),)
#
#     def next(self):
#         self.lines.dummyline[0] = self.data[0]
#         # self.lines.previous[0] = self.data[1]
#         # self.lines.value[0] = self.params.value
#
# class DummyInd1(bt.Indicator):
#     lines = ('dummyline', 'previous', 'value')
#     params = (('value', 5),)
#
#     def __init__(self):
#         self.sma=SimpleMovingAverage1()
#         self.dummy=DummyInd0()
#
#     def next(self):
#         self.lines.dummyline[0] = self.data[0]
#         # self.lines.previous[0] = self.data[1]
#         # self.lines.value[0] = self.params.value
#
# class DummyInd11(bt.Indicator):
#     lines = ('dummyline', 'previous', 'value')
#     params = (('value', 5),)
#
#     def __init__(self):
#         self.sma=SimpleMovingAverage1()
#         self.dummy=DummyInd0()
#
#     def next(self):
#         self.lines.dummyline[0] = self.data[0]
#         # self.lines.previous[0] = self.data[1]
#         # self.lines.value[0] = self.params.value
#
# class DummyInd(bt.Indicator):
#     lines = ('dummyline', 'sma', 'newline')
#     params = (('value', 5),)
#
#     # plotlines = dict(dummyline=dict(ls='--', _name="MyDummy"))
#     #plotlines=dict(dummyline=dict(_fill_lt=('sma', ('red', 0.5))))
#
#     def __init__(self):
#         self.lines.sma=SimpleMovingAverage1()
#         # self.dummy=DummyInd1()
#         # self.dummy=DummyInd11()
#
#         # self.plotinfo.plotname="TestInd"
#         # self.plotinfo.plotmaster=self.datas[2]
#         self.plotinfo.subplot=False
#
#     def next(self):
#         self.lines.dummyline[0] = self.data[0]
#         # self.lines.previous[0] = self.data[1]
#         # self.lines.value[0] = self.params.value
#
# # Create a Stratey
# class TestStrategy(bt.Strategy): # copied from Bactrader quick start guide
#
#     def log(self, txt, dt=None):
#         ''' Logging function fot this strategy'''
#         dt = dt or self.datas[0].datetime.date(0)
#         print('%s, %s' % (dt.isoformat(), txt))
#
#     def __init__(self):
#         # Keep a reference to the "close" line in the data[0] dataseries
#         self.dataclose = self.datas[0].close
#         self.dummy1=DummyInd(self.data0, self.data1, self.data2)
#         #self.dummy2=DummyInd(self.datas[0])
#         #self.sma=btind.SMA(20)
#
#         # To keep track of pending orders
#         self.order = None
#         self.notFin=True
#
#     def notify_order(self, order):
#         if order.status in [order.Submitted, order.Accepted]:
#             # Buy/Sell order submitted/accepted to/by broker - Nothing to do
#             return
#
#         # Check if an order has been completed
#         # Attention: broker could reject order if not enough cash
#         if order.status in [order.Completed]:
#             if order.isbuy():
#                 self.log('BUY EXECUTED, %.2f' % order.executed.price)
#             elif order.issell():
#                 self.log('SELL EXECUTED, %.2f' % order.executed.price)
#
#             self.bar_executed = len(self)
#
#         elif order.status in [order.Canceled, order.Margin, order.Rejected]:
#             self.log('Order Canceled/Margin/Rejected')
#
#         # Write down: no pending order
#         self.order = None
#
#     def next(self):
#         # Simply log the closing price of the series from the reference
#         #self.log('Close, %.2f' % self.dataclose[0])
#         # print("Dummy indicator:"+str(self.dummy1[0]))
#         # test_ind=self.dataclose[0]+self.dummy1[0]
#         # bt.indicator.LinePlotterIndicator(test_ind, name="Test indicator")
#
#         # Check if an order is pending ... if yes, we cannot send a 2nd one
#         if self.order:
#             return
#
#         # Check if we are in the market
#         if not self.position and self.notFin:
#
#             # # Not yet ... we MIGHT BUY if ...
#             # if self.dataclose[0] < self.dataclose[-1]:
#             #         # current close less than previous close
#             #
#             #         if self.dataclose[-1] < self.dataclose[-2]:
#             #             # previous close less than the previous close
#
#             # BUY, BUY, BUY!!! (with default parameters)
#             self.log('BUY CREATE, %.2f' % self.dataclose[0])
#
#             # Keep track of the created order to avoid a 2nd order
#             #self.order = self.sell(size=3)
#             self.order = self.buy(size=0.5)
#             #self.notFin=False
#
#         else:
#
#             # Already in the market ... we might sell
#             if len(self) >= (self.bar_executed + 2):
#                 # SELL, SELL, SELL!!! (with all possible default parameters)
#                 self.log('SELL CREATE, %.2f' % self.dataclose[0])
#
#                 # Keep track of the created order to avoid a 2nd order
#                 self.order = self.sell(data=self.datas[0])
#                 self.notFin=False
# #
# # # this strategy opens and closes orders in sequence to test the tradeTester
# # class MyStrategy(bt.Strategy):
# #     params = (
# #         ("sql_input", None),
# #         ("TUID", None),
# #         )
# #
# #     def __init__(self):
# #         self.orders=ordersManager(self.p.TUID)
# #         self.order=None
# #
# #     def next(self):
# #         if self.order: # if order already created then close it
# #             #raise ValueError("TEST")
# #             print("order closed")
# #             self.order.close_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), self.data.close[0], 10000.0)
# #             pack=packet(operations.close_order, self.order.TUID, self.order)
# #             self.p.sql_input.put(pack)
# #             self.order=None
# #         else: # if not then open new order
# #             print("order created, first bar is "+str(self.datas[0].lines.close[0])+" and second bar is "+str(self.datas[1].lines.close[0]))
# #             self.order=self.orders.new_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
# #             pack=packet(operations.open_order, self.order.TUID, self.order)
# #             self.p.sql_input.put(pack)
# #
# # class MyStrategy1(bt.Strategy):
# #     params = (
# #         ("sql_input", None),
# #         ("TUID", None),
# #         )
# #
# #     def __init__(self):
# #         self.orders=ordersManager(self.p.TUID)
# #         self.order=None
# #
# #     def next(self):
# #         if self.order: # if order already created then close it
# #
# #             self.order.close_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), self.data.close[0], 10000.0)
# #             pack=packet(operations.close_order, self.order.TUID, self.order)
# #             self.p.sql_input.put(pack)
# #             self.order=None
# #         else: # if not then open new order
# #             self.order=self.orders.new_order(str(dt.now().strftime("%Y-%m-%d %H:%M:%S")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
# #             pack=packet(operations.open_order, self.order.TUID, self.order)
# #             self.p.sql_input.put(pack)
# #
# # if __name__ == "__main__":
# #     contr=controller(r"C:\Users\User\Documents\Projektid\Python\tradeTester\development_materials\test_db.db")
# #     #contr.start()
# #     asset1=asset_set("ETHUSDT", "KUCOIN", [Interval.in_3_minute, Interval.in_5_minute])
# #     asset2=asset_set("ETHUSDT", "KUCOIN", [Interval.in_1_minute, Interval.in_3_minute])
# #     tuid1=contr.start_testrun("myTest1", MyStrategy, asset1, 10000) # strategy name must be unique and orders for that testrun must be removed from DB before running
# #     tuid2=contr.start_testrun("myTest2", MyStrategy, asset2, 10000)
# #     # tuid3=contr.start_testrun("myTest", MyStrategy1, "ETHUSDT", "KUCOIN", "3 minutes", 10000)
# #     contr.select_testrun(tuid2)
# #     t=threading.Thread(target=terminal, args=(contr.sql_output,))
# #     t.start()
# #     # print("Thread started, waiting...")
# #     # time.sleep(400)
# #     # print("Printing out from TUID 1...")
# #     # contr.select_testrun(tuid1)
# #     # time.sleep(300)
# #     # print("Printing testruns...")
# #     # print(contr.get_testruns())
# #     # print("Printing ticker data...")
# #     # print(contr.get_ticker_data(tuid1))
# #     # print("Printing order data...")
# #     # print(contr.get_orders(tuid2))
# #     # print("Stopping testrun 2...")
# #     # contr.stop_testrun(tuid2)
# #     time.sleep(180)
# #     print("Stopping all testruns...")
# #     contr.stop_all_testruns()
# #     #
# #     # datafeeds_list=[]
# #     # data_collector=tdr(True)
# #     #
# #     # asset_id1=data_collector.add_symbol("ETHUSDT", "KUCOIN", Interval.in_3_minute)
# #     # asset_id2=data_collector.add_symbol("ETHUSDT", "KUCOIN", Interval.in_5_minute)
# #     #
# #     # datafeeds_list.append(tld(data_collector, asset_id1))
# #     # datafeeds_list.append(tld(data_collector, asset_id2))
# #     #
# #     # cerebro = bt.Cerebro()
# #     # cerebro.addstrategy(testStrategy)
# #     # for feed in datafeeds_list: # add all data feeds to cerebro, each needs to be added with separate call to adddata() method
# #     #     cerebro.adddata(feed) 
# #     # cerebro.run()
#
# # import time
# # from tvDatafeedRealtime import tvDatafeedRealtime
# # from tvDatafeed import Interval
# #
# # def cb(data):
# #     print("Ticker set id "+str(data[0])+ " produced close price "+str(data[1].close))
# #
# # collector=tvDatafeedRealtime()
# # asset_id=collector.add_symbol("ETHUSDT", "KUCOIN", Interval.in_1_minute)
# # callback_ref=collector.add_callback(asset_id, cb)
# #
# # time.sleep(300)
# # print("deleting callback ref")
# # collector.del_callback(callback_ref)
# # time.sleep(20)
# # print("deleting symbol")
# # collector.del_symbol(asset_id)
#
# class OrderObserver(bt.observer.Observer): # observer to access bar data in Strategy
#     lines = ('dummy_line',)
#
#     def _get_indicators(self, ind_list):
#         for ind in ind_list:
#             if not importlib.util.find_spec(f".{ind.__class__.__name__}", package="backtrader.indicators"): # if indicator not part of backtrader indicators library (is custom)
#                 yield (ind.__class__.__name__, inspect.getfile(ind.__class__)) # indicator name, indicator modules full path and file name
#             if sub_ind_list := ind.getindicators(): # if indicator has sub indicators
#                 yield from self._get_indicators(sub_ind_list) # go one level deeper and perform same steps
#
#     def start(self):
#         # setup whatever connection is needed with SQL Manager here
#         # self.sql=self._owner.cerebro.observers[0][3]['sql']
#         inds=self._owner.getindicators()
#         for ind in inds:
#             # print(ind)
#             # print(ind.lines)
#             # print(ind.__class__.__name__)
#             if ind.plotinfo.plotmaster is not None:
#                 data_feed=ind.plotinfo.plotmaster
#             else:
#                 data_feed=ind.data
#
#             for index in range(len(ind.datas)): 
#                 if id(data_feed)==id(ind.datas[index]):
#                     data_index=index
#                     break
#
#             print(data_index)
#             print("got it")
#         #
#         # print("Printing indicator now")
#         # inds=[]
#         # for ind in self._get_indicators(self._owner.getindicators()):
#         #     if ind not in inds:
#         #         inds.append(ind)
#         #
#         # print(inds)
#
#         # for ind in self._owner.getindicators():
#         #     # line_names=ind._getlines()
#         #     # ind_name=type(ind).__name__
#         #     # STEPS:
#         #     # - loop through provided list
#         #     # - check if elemnt is custom indicator, if yes then yield indicator name and full filename_path
#         #     # - get the list of indicators (sub-indicators) for this element using getindicators() method
#         #     # - check that list is not empty, if it is not then function to re-call itself with this list with yield from staetemnt
#         #     for i in ind.getindicators():
#         #         if importlib.util.find_spec(f".{i.__class__.__name__}", package="backtrader.indicators"):
#         #             print("Integrated indicator")
#         #         else:
#         #             print("Custom indicator")
#         #     print(inspect.getfile(ind.__class__))
#
#     def next(self):
#         # print("Observer datas:"+str(type(self._owner.datas)))
#         # datetimes=[]
#         # for data in self._owner.datas:
#         #     datetimes.append(bt.num2date(data.datetime[0]))
#         # print(datetimes)
#         # datetimes.sort()
#         # # print(datetimes)
#         # exec_bar_dt=datetimes[-1]
#         # print(str(exec_bar_dt))
#         # # print("Observer datas:"+str(self._owner.dummy1[0]))
#         # # print("Observer: Close price of 3 minute interval: "+str(self._owner.datas[0].lines.close[0]))
#         # # print("Observer [orderspending]:"+str(self._owner._orderspending))
#         # # print("Observer [tradespending]:"+str(self._owner._tradespending))
#         # print("Observer [orderspending]:")
#         # for order in self._owner._orderspending:
#         #     # print(bt.num2date(order.dtopen))
#         #     print("Order status: "+order.Status[order.status])
#         #     print("Order created dt : "+str(bt.num2date(order.created.dt)))
#         #     # print("Order executed dt : "+str(bt.num2date(order.executed.dt)))
#         #
#         #     # print("Order created object : "+str(order.created))
#         #     # print("Order executed object : "+str(order.executed))
#         #     # print("Order data object : "+str(order.data)) # data is actual bar data not order data
#         #     # print("Order status: "+order.Status[order.status])
#         #     print("_________________________________")
#         # # print("Observer [tradespending]:"+str(self._owner._tradespending))
#         # for trade in self._owner._tradespending:
#         #     print(bt.num2date(trade.dtopen))
#         #     print("Trade status: "+str(trade.status)) # add .open_datetime  .ref
#         #     print("Trade data object: "+str(trade.data))
#         # TODO: look into plotting custom indicators; read Indicators - Development section in docs
#         print(inspect.getfile(self._owner.__class__))
#
#         for ind in self._owner.getindicators():
#             # line_names=ind._getlines()
#             # ind_name=type(ind).__name__
#             for i in ind.getindicators():
#                 if importlib.util.find_spec(f".{i.__class__.__name__}", package="backtrader.indicators"):
#                     print("Integrated indicator")
#                 else:
#                     print("Custom indicator")
#             print(inspect.getfile(ind.__class__))
#             # for line_name in line_names:
#             #     line=ind._getline(line_name)
#             #     print("Indicator "+ind_name+" line "+str(line_name)+" value is "+str(line[0]))
#                 # print(line.index[0])
#
#         # print(self._owner.datas.index) # TODO: need to be able to see a list of all available data feeds - datas is a Pandas object
#         # print("Observer: Close price of 5 minutes interval: "+str(self._owner.datas[1].lines.close[-1]))
#         # print(self.sql)
#         # for data in self._owner.datas:
#         #     print(data.lines.close[0])
#         # positions_list=list(self._owner.broker.positions.values())
#         # processed_pos_symbols=[]
#         # for position in self._owner.broker.positions.values():
#         #     # TODO: find a way how to tie position objects to specifc data feeds - index numbers?
#         #     index_num=positions_list.index(position)
#         #     symbol=self._owner.datas[index_num]._dataname.symbol[-1]
#         #     if symbol in processed_pos_symbols: # if we already have recorded position for this symbol:exchange pair
#         #         continue
#         #     else:
#         #         processed_pos_symbols.append(symbol) # mark that we already recorded this pair
#         #         print(symbol)
#         #         print(str(position.size))
#         position=self._owner.broker.getposition(data=self._owner.datas[0])
#         print(position.size)    
#         print(position.price) 
#
#         print("Observer: Broker cash size: "+str(self._owner.broker.getcash()))
#         print("Observer: Broker value size: "+str(self._owner.broker.getvalue()))
#         # print("Position: "+str(self._owner.broker.getposition()))
#
# tv=TvDatafeed()
# data3m=tv.get_hist("ETHUSDT", "KUCOIN", n_bars=50, interval=Interval.in_3_minute)
# data5m=tv.get_hist("ETHUSDT", "KUCOIN", n_bars=50, interval=Interval.in_5_minute)
# data15m=tv.get_hist("ETHUSDT", "BINANCE", n_bars=50, interval=Interval.in_3_minute)
# print(type(data15m) == pandas.DataFrame)
#
# cerebro = bt.Cerebro(stdstats=False) # argument stdstats removes the observers for broker, trades and buy/sell
# # cerebro.sql_ref="test"
# cerebro.addobserver(OrderObserver, sql="test")
# # cerebro.addobserver(OrderObserver1, sql="test1")
# #cerebro.addstrategy(mys.smaCrossAdx,risk_reward_ratio=3,adx_level=30, risk_percent=10)
#
# cerebro.addstrategy(TestStrategy)
# cerebro.run()
#
# pd_data3m=btfeeds.PandasData(dataname=data3m) # convert data into backtester data format
# pd_data5m=btfeeds.PandasData(dataname=data5m) # convert data into backtester data format
# pd_data15m=btfeeds.PandasData(dataname=data15m) # convert data into backtester data format
#
# cerebro.adddata(pd_data3m)
# cerebro.adddata(pd_data5m)
# cerebro.adddata(pd_data15m)
#
# cerebro.broker.setcash(10000.0)
#
# cerebro.run(runonce=False)
# cerebro.plot(style='candlestick', barup='green', bardown='red')
