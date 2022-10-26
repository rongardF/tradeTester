'''
Created on 4. okt 2022

@author: User
'''
import backtrader as bt
import bt.num2date as num2date
from livetrader import ObserverPackage, Order, Indicator, Line, BrokerData

class SqlObserver(bt.observer.Observer): 
    '''
    Custom observer to extract price (OHCLV), TA indicator, 
    orders, trades and broker data. Extracted data will be 
    sent to SQL database (SQL Manager) or storing. This 
    observer will be added by default to all strategies 
    running in tradeTester. 
    '''
    lines = ('dummy_line',)
    
    def start(self):
        # setup whatever connection is needed with SQL Manager here
        self.sql=self._owner.cerebro.observers[0][3]['sql'] # get reference to SQL Manager from observer parameters
        self.tuid=self._owner.cerebro.observers[0][3]['tuid']
    
    def next(self):
        # find out what is the current datetime
        datetimes=[]
        for data in self._owner.datas:
            datetimes.append(bt.num2date(data.datetime[0]))
        datetimes.sort()
        curr_dt=datetimes[-1]
        
        package=ObserverPackage()
        
        # extract orders data
        for order in self._owner._orderspending:
            executed_dt=num2date(order.executed.dt) if order.executed.dt else None
            price_executed=order.executed.price if order.executed.dt else None
            size_executed=order.executed.size if order.executed.dt else None
            package.orders.append(Order(self.tuid, order.ref, num2date(order.created.dt), executed_dt, \
                                 order.ordtype, order.created.price, price_executed, order.created.size, \
                                 size_executed, order.plimit, order.exectype, order.executed.value, \
                                 order.executed.comm, order.executed.pnl))
        
        # extract indicators and their lines
        for ind in self._owner.getindicators(): # loop through all indicators
            indicator=Indicator(self.tuid, type(ind).__name__)
            line_names=ind._getlines() # get lines for this indicator
            for line_name in line_names: # and loop through all lines
                line=ind._getline(line_name)
                indicator.lines.append(Line(line_name, curr_dt, line[0])) # create line object and append to indicator
            package.indicators.append(indicator)
            
        # get the broker state (cash, value, position size, avg_price) after all orders have been executed
        # bt only tracks position for data0 correctly - with other datas there seems to be some issue
        package.broker_data=BrokerData(self.tuid, curr_dt, self._owner.broker.getvalue(), \
                                       self._owner.broker.getcash(), \
                                       self._owner.broker.getposition(data=self._owner.datas[0]).size, \
                                       self._owner.broker.getposition(data=self._owner.datas[0]).price)
        
        self.sql.put(package) # send package to SQL Manager    
        