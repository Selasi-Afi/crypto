import asyncio
from threading import Timer
from bitfinex_connector.bitfinex_client import BitfinexClient
from coinbase_connector.coinbase_client import CoinbaseClient
from common_components import configs
from datetime import datetime as dt
from multiprocessing import Process
import time


class Crypto(Process):

    def __init__(self, symbols):
        super(Crypto, self).__init__()
        self.symbols = symbols
        self.timer_frequency = configs.SNAPSHOT_RATE
        self.workers = dict()
        self.current_time = dt.now()
        self.daemon = False

    # noinspection PyTypeChecker
    def timer_worker(self, coinbaseClient, bitfinexClient):
        """
        Thread worker to be invoked every N seconds (e.g., configs.SNAPSHOT_RATE)
        :return: void
        """
        Timer(self.timer_frequency, self.timer_worker, args=(coinbaseClient, bitfinexClient,)).start()
        self.current_time = dt.now()

        if coinbaseClient.book.done_warming_up() & bitfinexClient.book.done_warming_up():
            print('%s >> %s' % (coinbaseClient.sym, coinbaseClient.book))
        else:
            if coinbaseClient.book.done_warming_up():
                print('Coinbase - %s is warming up' % coinbaseClient.sym)
            if bitfinexClient.book.done_warming_up():
                print('Bitfinex - %s is warming up' % bitfinexClient.sym)

    # noinspection PyTypeChecker
    def run(self):
        """
        Processes market data subscription per crypto pair (e.g., BTC-USD)
        :return: void
        """
        coinbase, bitfinex = self.symbols
        self.workers[coinbase], self.workers[bitfinex] = CoinbaseClient(coinbase), BitfinexClient(bitfinex)
        self.workers[coinbase].start(), self.workers[bitfinex].start()
        Timer(5.0, self.timer_worker, args=(self.workers[coinbase], self.workers[bitfinex],)).start()

        tasks = asyncio.gather(*[self.workers[sym].subscribe() for sym in self.workers.keys()])
        loop = asyncio.get_event_loop()
        print('Crypto Gathered %i tasks' % len(self.workers.keys()))

        try:
            loop.run_until_complete(tasks)
            loop.close()
            [self.workers[sym].join() for sym in self.workers.keys()]
            print('Crypto: loop closed.')

        except KeyboardInterrupt as e:
            print("Crypto: Caught keyboard interrupt. Canceling tasks... %s" % e)
            tasks.cancel()
            loop.close()
            [self.workers[sym].join() for sym in self.workers.keys()]

        finally:
            loop.close()
            print('\nCrypto: Finally done.')


if __name__ == "__main__":
    """
    Entry point of application
    """
    for coinbase, bitfinex in configs.BASKET:
        Crypto((coinbase, bitfinex)).start()
        print('\nProcess started up for %s' % coinbase)
        time.sleep(9)
