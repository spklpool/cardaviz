from threading import Lock

class ThreadSafeDictOfPoolJson():
    def __init__(self):
        self.inner_lock = Lock()
        with self.inner_lock:
            self.inner_dict = {}

    def keys(self):
        return self.inner_dict.keys()

    def update(self, ticker, json):
        with self.inner_lock:
            self.inner_dict[ticker] = json

    def __getitem__(self, ticker):
        with self.inner_lock:
            return self.inner_dict[ticker]

    def __setitem__(self, ticker, json):
        with self.inner_lock:
            self.inner_dict[ticker] = json

    def __repr__(self):
        return 'ThreadSafeDictOfPoolJson({})'.format(self.inner_dict)

