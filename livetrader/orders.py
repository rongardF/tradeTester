

class orders(object):
    
    def __init__(self, TUID, order_id_starting=0): # user can specify the starting value for order_id (incase we are going from backtest to forward test)
        self.order_id=order_id_starting
        self.TUID=TUID
    
    def __next__(self):
        new_order_id=self.order_id
        self.order_id += 1
        return new_order_id
    
    def new_order(self, open_datetime, order_type, entry_price, position_size, stop_loss_price, take_profit_price, open_account_size): 
        new_order_id=self.__next__()  
        new_order=order(new_order_id, self.TUID, open_datetime, order_type, entry_price, position_size, stop_loss_price, \
                        take_profit_price, open_account_size)
        
        return new_order
        
class order(object):
    
    def __init__(self, order_id, TUID, open_datetime, order_type, entry_price, position_size, stop_loss_price, \
                 take_profit_price, open_account_size):
        self.order_id=order_id # this must be iterator and is automatically iterated
        self.TUID=TUID
        self.state="OPEN" # maybe we can use enumerator here?
        self.open_datetime=open_datetime # this will be datetime type
        self.close_datetime="NULL"
        self.order_type=order_type
        self.entry_price=entry_price
        self.close_price="NULL"
        self.position_size=position_size
        self.stop_loss_price=stop_loss_price
        self.take_profit_price=take_profit_price
        self.open_account_size=open_account_size
        self.close_account_size="NULL"
    
    def close_order(self, close_datetime, close_price, close_account_size):
        self.close_datetime=close_datetime
        self.close_price=close_price
        self.close_account_size=close_account_size
        self.state="CLOSED"
    
    def get_sql_params(self): # this method returns a valid SQL parameters tuple
        if self.state == "OPEN":
            return (self.order_id, self.TUID, self.state, self.open_datetime, self.close_datetime, \
                    self.order_type, self.entry_price, self.close_price, self.position_size, self.stop_loss_price, \
                    self.take_profit_price, self.open_account_size, self.close_account_size)
        else:
            return (self.state, self.close_datetime, self.close_price, self.close_account_size, self.TUID, self.order_id)
    
    def get_id(self):
        return self.TUID