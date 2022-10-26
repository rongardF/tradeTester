
# SQLite3 statements used to create the ER schematics tables
sql_tables_statements=["CREATE TABLE modules (module_id INTEGER PRIMARY KEY, type INTEGER NOT NULL, blob_hash INTEGER NOT NULL, file BLOB NOT NULL)", \
                       "CREATE TABLE testruns (tuid INTEGER PRIMARY KEY, name TEXT NOT NULL, start_datetime TEXT NOT NULL, end_datetime TEXT, start_account REAL NOT NULL, end_account REAL, broker_commission REAL NOT NULL, module_id INTEGER NOT NULL, FOREIGN KEY(module_id) REFERENCES modules(module_id))", \
                       "CREATE TABLE indicators (indicator_id INTEGER PRIMARY KEY, indicator_name TEXT NOT NULL, module_id INTEGER NOT NULL, FOREIGN KEY(module_id) REFERENCES modules(module_id))", \
                       "CREATE TABLE sub_indicators_list (id INTEGER PRIMARY KEY, indicator_id INTEGER NOT NULL, sub_indicator_list_id INTEGER NOT NULL, FOREIGN KEY(indicator_id) REFERENCES indicators(indicator_id), FOREIGN KEY(sub_indicator_list_id) REFERENCES indicators(indicator_id))", \
                       "CREATE TABLE testrun_indicators (testrun_indicator_id INTEGER PRIMARY KEY, indicator_id INTEGER NOT NULL, tuid INTEGER NOT NULL, testrun_indicator_name TEXT NOT NULL, FOREIGN KEY(indicator_id) REFERENCES indicators(indicator_id), FOREIGN KEY(tuid) REFERENCES testruns(tuid))", \
                       "CREATE TABLE indicator_lines (line_id INTEGER PRIMARY KEY, testrun_indicator_id INTEGER NOT NULL, line_name TEXT NOT NULL, FOREIGN KEY(testrun_indicator_id) REFERENCES testrun_indicators(testrun_indicator_id))", \
                       "CREATE TABLE lines_values (value_id INTEGER PRIMARY KEY, line_id INTEGER NOT NULL, dt TEXT NOT NULL, value REAL NOT NULL, FOREIGN KEY(line_id) REFERENCES indicator_lines(line_id))", \
                       "CREATE TABLE lines_plotinfo (line_id INTEGER PRIMARY KEY, plotskip INTEGER NOT NULL, plotvalue INTEGER NOT NULL, plotvaluetag INTEGER NOT NULL, name TEXT, skipnan INTEGER NOT NULL, samecolor INTEGER NOT NULL, method TEXT NOT NULL, other_line_id INTEGER, other_line_value REAL, color TEXT NOT NULL, transparency REAL , FOREIGN KEY(line_id) REFERENCES indicator_lines(line_id), FOREIGN KEY(other_line_id) REFERENCES indicator_lines(line_id))", \
                       "CREATE TABLE datas (data_id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, exchange TEXT NOT NULL, interval INTEGER NOT NULL)", \
                       "CREATE TABLE testrun_indicators_plotinfo (testrun_indicator_id INTEGER PRIMARY KEY, plot INTEGER NOT NULL, subplot INTEGER NOT NULL, plotname TEXT, plotabove INTEGER NOT NULL, plotlinelabels INTEGER NOT NULL, plotlinevalues INTEGER NOT NULL, plotvaluetags INTEGER NOT NULL, plotymargin REAL NOT NULL, plotylimited INTEGER NOT NULL, plotmaster_data_id INTEGER, FOREIGN KEY(testrun_indicator_id) REFERENCES testrun_indicators(testrun_indicator_id), FOREIGN KEY(plotmaster_data_id) REFERENCES datas(data_id))",
                       "CREATE TABLE plothlines_lists (id INTEGER PRIMARY KEY, plothlines_list_id INTEGER NOT NULL, value REAL NOT NULL, FOREIGN KEY(plothlines_list_id) REFERENCES testrun_indicators_plotinfo(testrun_indicator_id))", \
                       "CREATE TABLE plotyticks_lists (id INTEGER PRIMARY KEY, plotyticks_list_id INTEGER NOT NULL, value REAL NOT NULL, FOREIGN KEY(plotyticks_list_id) REFERENCES testrun_indicators_plotinfo(testrun_indicator_id))", \
                       "CREATE TABLE plotyhlines_lists (id INTEGER PRIMARY KEY, plotyhlines_list_id INTEGER NOT NULL, value REAL NOT NULL, FOREIGN KEY(plotyhlines_list_id) REFERENCES testrun_indicators_plotinfo(testrun_indicator_id))", \
                       "CREATE TABLE testrun_datas_list (id INTEGER PRIMARY KEY, tuid INTEGER NOT NULL, data_id INTEGER NOT NULL, FOREIGN KEY(tuid) REFERENCES testruns(tuid), FOREIGN KEY(data_id) REFERENCES datas(data_id))", \
                       "CREATE TABLE broker_datas (id INTEGER PRIMARY KEY, tuid INTEGER NOT NULL, dt TEXT NOT NULL, value REAL NOT NULL, cash REAL NOT NULL, position_size REAL NOT NULL, avg_price REAL NOT NULL, FOREIGN KEY(tuid) REFERENCES testruns(tuid))", \
                       "CREATE TABLE bars (bar_id INTEGER PRIMARY KEY, data_id INTEGER NOT NULL, dt TEXT NOT NULL, close_price REAL NOT NULL, open_price REAL NOT NULL, high_price REAL NOT NULL, low_price REAL NOT NULL, volume REAL NOT NULL, FOREIGN KEY(data_id) REFERENCES datas(data_id))", \
                       "CREATE TABLE orders (order_id INTEGER PRIMARY KEY, tuid INTEGER NOT NULL, order_ref INTEGER NOT NULL, created_datetime TEXT NOT NULL, executed_closed_datetime TEXT NOT NULL, order_type INTEGER NOT NULL, price_created REAL NOT NULL, price_executed REAL, size_created INTEGER NOT NULL, size_executed INTEGER, plimit REAL, execution_type INTEGER NOT NULL, value_executed REAL, commission REAL, pnl REAL, FOREIGN KEY(tuid) REFERENCES testruns(tuid))", \
                       "CREATE TABLE order_notifications (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, dt TEXT NOT NULL, status INTEGER NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(order_id))"]

# INSERT statements
sql_insert_testrun_statement="INSERT INTO testruns VALUES(NULL, ?, ?, NULL, ?, NULL, ?, ?)"
sql_insert_data="INSERT INTO datas VALUES(NULL, ?, ?, ?)"
sql_insert_testrun_datas="INSERT INTO testrun_datas_list VALUES(NULL, ?, ?)"
sql_insert_module="INSERT INTO modules VALUES(NULL, ?, ?)"
sql_insert_bar="INSERT INTO bars VALUES(NULL, ?, ?, ?, ?, ?, ?, ?)"

# SELECT statements
sql_select_data="SELECT * FROM datas WHERE symbol=? AND exchange=? AND interval=?"
sql_select_module_hash="SELECT * FROM datas WHERE hash=?"