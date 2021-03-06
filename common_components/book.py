from abc import ABC, abstractmethod
from datetime import datetime as dt
from sortedcontainers import SortedDict
from common_components import configs
import pandas as pd
import pytz as tz


class Book(ABC):

    def __init__(self, sym, side):
        self.price_dict = SortedDict()
        self.order_map = dict()
        self.side = side
        self.sym = sym
        self.warming_up = True  # this value needs to be set within the orderbook class
        self.max_book_size = configs.MAX_BOOK_ROWS

    def __str__(self):
        if self.warming_up:
            message = 'warming up'
        elif self.side == 'asks':
            ask_price, ask_value = self.get_ask()
            message = '%s x %s' % (str(round(ask_price, 2)), str(round(ask_value['size'], 2)))
        else:
            bid_price, bid_value = self.get_bid()
            message = '%s x %s' % (str(round(bid_value['size'], 2)), str(round(bid_price, 2)))
        return message

    def clear(self):
        """
        Reset price tree and order map
        :return: void
        """
        self.price_dict = SortedDict()
        self.order_map = dict()
        self.warming_up = True

    def create_price(self, price):
        """
        Create new node
        :param price:
        :return:
        """
        self.price_dict[price] = {'size': float(0), 'count': int(0)}

    def remove_price(self, price):
        """
        Remove node
        :param price:
        :return:
        """
        del self.price_dict[price]

    def receive(self, msg):
        """
        add incoming orders to order map
        :param msg:
        :return:
        """
        pass

    @abstractmethod
    def insert_order(self, msg):
        """
        Create new node
        :param msg:
        :return:
        """
        pass

    @abstractmethod
    def match(self, msg):
        """
        Change volume of book
        :param msg:
        :return:
        """
        pass

    @abstractmethod
    def change(self, msg):
        """
        Update inventory
        :param msg:
        :return:
        """
        pass

    @abstractmethod
    def remove_order(self, msg):
        """
        Done messages result in the order being removed from map
        :param msg:
        :return:
        """
        pass

    def get_ask(self):
        """
        Best offer
        :return: inside ask
        """
        if len(self.price_dict) > 0:
            return self.price_dict.items()[0]
        else:
            return 0.0

    def get_bid(self):
        """
        Best bid
        :return: inside bid
        """
        if len(self.price_dict) > 0:
            return self.price_dict.items()[-1]
        else:
            return 0.0

    def _get_asks_to_list(self):
        """
        Transform order book to dictionary with 3 lists:
            1- ask prices
            2- cumulative ask volume at a given price
            3- number of orders resting at a given price
        :return: dictionary
        """
        prices, sizes, counts = list(), list(), list()
        counter = 0
        for k, v in self.price_dict.items():
            counter += 1
            if counter > self.max_book_size:
                break
            prices.append(k)
            sizes.append(v['size'])
            counts.append(v['count'])

        return pd.DataFrame(data={'ask_price': prices, 'ask_size': sizes, 'ask_count': counts},
                            index=[dt.now(tz=tz.timezone('US/Eastern')) for _ in range(counter - 1)])

    def _get_bids_to_list(self):
        """
        Transform order book to dictionary with 3 lists:
            1- bid prices
            2- cumulative bid volume at a given price
            3- number of orders resting at a given price
        :return: dictionary
        """
        prices, sizes, counts = list(), list(), list()
        counter = 0
        for k, v in reversed(self.price_dict.items()):
            counter += 1
            if counter > self.max_book_size:
                break
            prices.append(k)
            sizes.append(v['size'])
            counts.append(v['count'])

        return pd.DataFrame(data={'bid_price': prices, 'bid_size': sizes, 'bid_count': counts},
                            index=[dt.now(tz=tz.timezone('US/Eastern')) for _ in range(counter - 1)])
