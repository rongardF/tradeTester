Description
==========

TradeTester is a tool to test various trading strategies both on historic 
data and on live data streams. Tool uses `backtrader <https://www.backtrader.com/>` to provide the comprehensive 
testing environment and `tvDatafeed <https://pypi.org/project/tvdatafeed/>` to easily (and without charge) retrieve both 
historic and live ticker data from `TradingView <https://www.tradingview.com/>` platform.

TradeTester is provides controller through which user can create and manage testruns. 
Testruns are essentially separate threads executing backtrader (cerebro) with user specified
strategy. Strategy is executed on live ticker data which is retrieved from TradingView. Live
data is retrieved using modified tvDatafeed code base which, instead of retrieving historic
data, monitors specified assets for new data and once it is released retrieves it and feeds
into testruns (Cerebros running stratgies). 

The data IS NOT LIVE in the sense that it has a delay. TradeTester is not intended to perform
automated trading, but is visioned to perform automated stratgy testing and (in hoepfully in
the future) ranking different stragies in real-time based on some metrics.

Features
==========

TradeTester is still in development as of now, but following features have been
implmented (but not fully tested):

- Basic SQL database (on local machine) to save all the orders and testruns
- Retrieving live ticker data from TradingView using tvDatafeed
- Running separate backtrader strategies in thread concurrently (testruns)
- Simple controller module to start and stop running new strategies in a single
  TradeTester application (don't need to run multiple backtrader scripts to test
  multiple stratgies)
	  
Features that are planned to add in the future:

- GUI through which user can add strategies that they want to test and also see
  live statistics and ticker/order data about running stratgies. Vision is to have
  some metrics which will quickly show which stratgies is most successful and there
  will be a ranking based on that
- Seamless transition from backtesting (historic data) to live testing (on data live 
  streams). Currently the backtesting part must be done separtly and TradeTester only 
  support live testing.
	
How to use
==========

	Currently the main.py acts as a testbench and an example code. In the future (once GUI
	is added) this will change and it will act as a boot up module.

The controller module is meant to act as a central controller through which user can add
and manage testruns. As TradeTester includes an SQL database for saving orders then controller
must be initialized by providing a path and a Sqlite3 database name. TradeTester will create
a database in that location with that name. Each instance of controller will have its own
database. In the future it is visioned that there will be only one instance of controller
running 24/7 and user will use it to add and removed new testruns (strategies).

::

  contr=controller(r"C:\Users\User\Documents\tradeTester\development_materials\testDB.db")

After creating a controller instance user can use that to add new testruns via method 
``start_testrun()`` and providing unique name for testrun, strategy class template,
asset, exchange/market, timeframe interval and starting account size.

::

  tuid=contr.start_testrun("myTest1", MyStrategy, "ETHUSDT", "KUCOIN", Interval.in_1_minute, 10000)

This method will return an integer (TUID - Testrun Unique ID) which can be used later to
uniquely reference that testrun.

TradeTester is designed with an idea of having GUI in the future. Because of that reason 
the logic is that testruns (strategies) will send all orders to SQLManager instance which
takes care of saving them into database. The GUI will display data (orders, ticker data etc.)
for one particular testrun at any given time. This is set by setting the streamer in SQLManager
(via controller instance). The streamer setting means that SQLManager will propagate only that
testrun related data to GUI. Propagating data is done via Queues.

::

  contr.select_testrun(tuid1)