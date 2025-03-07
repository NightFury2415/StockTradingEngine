MAX_TICKERS = 1024

class Order:
    __slots__ = ('order_type', 'ticker', 'quantity', 'price', 'next')
    def __init__(self, order_type, ticker, quantity, price):
        self.order_type = order_type
        self.ticker = ticker
        self.quantity = quantity
        self.price = price
        self.next = None

class StockExchange:
    def __init__(self):
        # Lock-free order books for 1024 tickers (buy/sell as linked lists)
        self.buy_orders = [None] * MAX_TICKERS  # Head pointers for buys (sorted descending)
        self.sell_orders = [None] * MAX_TICKERS # Head pointers for sells (sorted ascending)

    def addOrder(self, order_type, ticker, quantity, price):
        new_order = Order(order_type, ticker, quantity, price)
        if order_type == 'Buy':
            # Lock-free insertion into buy_orders (sorted descending)
            while True:
                head = self.buy_orders[ticker]
                if head and head.price >= new_order.price:
                    new_order.next = head
                    if self._cas_buy_head(ticker, head, new_order):
                        break
                else:
                    new_order.next = head
                    if self._cas_buy_head(ticker, head, new_order):
                        break
        else:
            # Lock-free insertion into sell_orders (sorted ascending)
            while True:
                head = self.sell_orders[ticker]
                if head and head.price <= new_order.price:
                    new_order.next = head
                    if self._cas_sell_head(ticker, head, new_order):
                        break
                else:
                    new_order.next = head
                    if self._cas_sell_head(ticker, head, new_order):
                        break
        self.matchOrder(ticker)

    def _cas_buy_head(self, ticker, expected, new):
        # Simulate CAS for buy_orders head
        if self.buy_orders[ticker] is expected:
            self.buy_orders[ticker] = new
            return True
        return False

    def _cas_sell_head(self, ticker, expected, new):
        # Simulate CAS for sell_orders head
        if self.sell_orders[ticker] is expected:
            self.sell_orders[ticker] = new
            return True
        return False

    def matchOrder(self, ticker):
        while True:
            buy_head = self.buy_orders[ticker]
            sell_head = self.sell_orders[ticker]
            if not buy_head or not sell_head or buy_head.price < sell_head.price:
                break
            matched_qty = min(buy_head.quantity, sell_head.quantity)
            buy_head.quantity -= matched_qty
            sell_head.quantity -= matched_qty
            print(f"Matched {matched_qty} shares of ticker {ticker} at {sell_head.price}")
            if buy_head.quantity <= 0:
                self.buy_orders[ticker] = buy_head.next
            if sell_head.quantity <= 0:
                self.sell_orders[ticker] = sell_head.next

    def simulateOrders(self):
        orders = [
            ('Buy', 0, 50, 100),   # Buy 50 shares of ticker 0 at price 100
            ('Sell', 0, 30, 100),  # Sell 30 shares of ticker 0 at price 100
            ('Buy', 1, 40, 150),   # Buy 40 shares of ticker 1 at price 150
            ('Sell', 1, 40, 150),  # Sell 40 shares of ticker 1 at price 150
            ('Buy', 2, 25, 200),   # Buy 25 shares of ticker 2 at price 200
            ('Sell', 2, 25, 200),  # Sell 25 shares of ticker 2 at price 200
            ('Buy', 3, 100, 250),  # Buy 100 shares of ticker 3 at price 250
            ('Sell', 3, 100, 250), # Sell 100 shares of ticker 3 at price 250
            ('Buy', 4, 60, 300),   # Buy 60 shares of ticker 4 at price 300
            ('Sell', 4, 60, 300),  # Sell 60 shares of ticker 4 at price 300
        ]

        for order_type, ticker, quantity, price in orders:
            self.addOrder(order_type, ticker, quantity, price)

exchange = StockExchange()
exchange.simulateOrders()
