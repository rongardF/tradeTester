Description
==========

TradeTester is a tool to test various trading strategies both on historic 
data and on live data streams. Tool uses backtrader to provide the comprehensive 
testing environment and tvDatafeed to easily (and without charge) retrieve both 
historic and live ticker data from TradingView platform.

Features
==========

TradeTester is still in development as of now, but following features have been
implemnted (but not fully tested):

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



