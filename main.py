'''
'''
import threading
import backtrader as bt
import traceback
import time
from datetime import datetime as dt
from tvDatafeed import Interval

from livetrader.orders import orders
from livetrader.sqlManager import operations, packet
from livetrader.controller import controller

def terminal(queue):
    while True:
        pack=queue.get()
        # print out info from data
        order=pack.get_data()
        print("Order "+order.state+" with entry price "+str(order.entry_price)+" and close price "+str(order.close_price))

# this strategy opens and closes orders in sequence to test the tradeTester
class MyStrategy(bt.Strategy):
    params = (
        ("sql_input", None),
        ("TUID", None),
        )
    
    def __init__(self):
        self.orders=orders(self.p.TUID)
        self.order=None

    def next(self):
        if self.order: # if order already created then close it
            #raise ValueError("TEST")
            self.order.close_order(str(dt.now().strftime("%d-%m-%y %H:%M")), self.data.close[0], 10000.0)
            pack=packet(operations.close_order, self.order.TUID, self.order)
            self.p.sql_input.put(pack)
            self.order=None
        else: # if not then open new order
            self.order=self.orders.new_order(str(dt.now().strftime("%d-%m-%y %H:%M")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
            pack=packet(operations.open_order, self.order.TUID, self.order)
            self.p.sql_input.put(pack)
            
class MyStrategy1(bt.Strategy):
    params = (
        ("sql_input", None),
        ("TUID", None),
        )
    
    def __init__(self):
        self.orders=orders(self.p.TUID)
        self.order=None

    def next(self):
        if self.order: # if order already created then close it
            self.order.close_order(str(dt.now().strftime("%d-%m-%y %H:%M")), self.data.close[0], 10000.0)
            pack=packet(operations.close_order, self.order.TUID, self.order)
            self.p.sql_input.put(pack)
            self.order=None
        else: # if not then open new order
            self.order=self.orders.new_order(str(dt.now().strftime("%d-%m-%y %H:%M")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
            pack=packet(operations.open_order, self.order.TUID, self.order)
            self.p.sql_input.put(pack)

if __name__ == "__main__":
    contr=controller(r"C:\Users\User\Documents\Projektid\Python\tradeTester\development_materials\test_db.db")
    #contr.start()
    tuid1=contr.start_testrun("myTest1", MyStrategy, "ETHUSDT", "KUCOIN", Interval.in_1_minute, 10000) # strategy name must be unique and orders for that testrun must be removed from DB before running
    tuid2=contr.start_testrun("myTest2", MyStrategy1, "ETHUSDT", "KUCOIN", Interval.in_1_minute, 10000)
    #tuid3=contr.start_testrun("myTest3", MyStrategy, "ETHUSDT", "KUCOIN", Interval.in_3_minute, 10000)
    contr.select_testrun(tuid1)
    t=threading.Thread(target=terminal, args=(contr.sql_output,))
    t.start()
    print("Thread started, waiting...")
    time.sleep(120)
    testrun_list=contr.get_testruns()
    print(testrun_list)
    print("Stopping testrun1")
    contr.stop_testrun(tuid1)
    print("Deleting testrun1")
    contr.del_testrun(tuid1)
    print("Deleting testrun2")
    contr.del_testrun(tuid2)
    print("Deleted")
    print("Starting new testrun")
    tuid3=contr.start_testrun("myTest3", MyStrategy1, "ETHUSDT", "KUCOIN", Interval.in_3_minute, 10000)
    time.sleep(190)
    contr.stop_testrun(tuid3)
    print("Waiting...")
    time.sleep(300)