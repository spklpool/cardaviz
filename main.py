import os
import time
import signal
import logging
import simplejson as json
from flask import Flask, render_template
from thread_safe_objects import ThreadSafeDictOfPoolJson
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DataFileChangedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.json'):
            time.sleep(0.1)
            logging.info(f'event type: {event.event_type}  path : {event.src_path}')
            try:
                pool_json = json.load(open(event.src_path))
                map_of_pool_jsons[pool_json['ticker']] = pool_json
            except Exception as e:
                logging.error(f'{e}. Continuing execution...')


logging.basicConfig(level=logging.INFO, force=True)

app = Flask(__name__)

map_of_pool_jsons = ThreadSafeDictOfPoolJson()

directory = 'data/'
#directory = '/var/www/html/data/'
logging.info('starting initial load of datadirectory [' + directory + '] for changes')
all_files = os.listdir(directory)
for filename in all_files:
    pool_file = os.path.join(directory, filename)
    if os.path.isfile(pool_file):
        pool_json = json.load(open(pool_file))
        map_of_pool_jsons[pool_json['ticker']] = pool_json

logging.info('starting to monitor directory [' + directory + '] for changes')
event_handler = DataFileChangedHandler()
observer = Observer()
observer.schedule(event_handler, path=directory, recursive=False)
observer.start()
logging.info('directory monitoring started')

original_handler = signal.getsignal(signal.SIGINT)

def sigint_handler(signum, frame):
    logging.info("interrupt received")
    original_handler(signum, frame)

try:
    signal.signal(signal.SIGINT, sigint_handler)
except ValueError as e:
    logging.error(f'{e}. Continuing execution...')


@app.route("/sparkler")
def sparkler():
    return render_template('sparkler.html')

@app.route("/thumbnail/<pool_ticker>")
def thumbnail(pool_ticker):
    return render_template('thumbnail.html', pool_ticker=pool_ticker.upper())

@app.route("/pools/<pool_ticker>")
def get_pool(pool_ticker):
    return render_template('perfchart.html', pool_ticker=pool_ticker.upper())

@app.route("/")
def get_pool_search():
    return render_template('pool_search.html')

@app.route("/performers")
def get_underappreciated_performers():
    pools = []
    tickers_json = json.load(open('static/tickers.json'))
    for (pool_ticker, pool_id) in tickers_json.items():
        pool = {}
        pool['cumulative_diff'] = 0
        pool['cumulative_epochs'] = 0
        pool['cumulative_blocks'] = 0
        pool['live_stake'] = 0
        pool['ticker'] = pool_ticker
        pool_file = directory + "/" + pool_ticker.upper() + ".json"
        try:
            pool_json = json.load(open(pool_file))
            for epoch in pool_json['epochs']:
                epoch_diff = epoch['actual'] - epoch['expected']
                pool['cumulative_diff'] += epoch_diff
                pool['cumulative_epochs'] += 1
                pool['cumulative_blocks'] += epoch['actual']
                pool['live_stake'] = epoch['pool_stake']
                pool['total_stake'] = epoch['total_stake']
            if pool['live_stake'] > 0:
                pool['block_performance'] = pool['cumulative_diff'] * pool['cumulative_blocks']
                pool['epochs_performance'] = pool['cumulative_diff'] * pool['cumulative_epochs']
                pool['total_performance'] = pool['cumulative_diff'] * pool['cumulative_blocks'] * pool['cumulative_epochs']
                pool['underappreciated'] = pool['cumulative_diff'] * pool['cumulative_epochs'] / (pool['live_stake'] / pool['total_stake'])
                pools.append(pool)
        except (Exception) as error:
            print("Unable to load " + pool_ticker)
            print(repr(error))

    performers = []
    sorted_by_underappreciated_performance = sorted(pools, key=lambda d: d['underappreciated'], reverse=True)
    rank = 0
    for pool in sorted_by_underappreciated_performance:
        if rank < 10:
            if pool['live_stake'] > (10000 * 1000000):
                if pool['cumulative_blocks'] > 5:
                    current_performer = {}
                    rank += 1
                    current_performer['rank'] = rank
                    current_performer['ticker'] = pool['ticker']
                    performers.append(current_performer)

    return render_template('underappreciated_performers.html', pools=performers)

@app.route("/data/<pool_ticker>.json")
def get_pool_epochs(pool_ticker):
    return map_of_pool_jsons[pool_ticker.upper()]


