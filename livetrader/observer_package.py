from collections import namedtuple

ObserverPackage=namedtuple("ObserverPackage", "orders indicators broker_data", defaults=[[], [], None])
BrokerData=namedtuple("BrokerData", "tuid dt value cash")
#Trade=namedtuple("Trade", "tuid trade_ref status size price value comnission pnl pnlcomm trade_opened_dt trade_closed_dt")
Order=namedtuple("Order", "tuid order_ref created executed_closed order_type price_created price_executed size_created size_executed plimit execution_type value_executed commission pnl")
Indicator=namedtuple("Indicator", "tuid indicator_name lines", defaults=[None, None, []])
Line=namedtuple("Line", "line_name created_dt value")
#Position=namedtuple("Position", "tuid dt symbol value")