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

@app.route("/ranking")
def get_ranking():
    pools = []
    for ticker in map_of_pool_jsons.keys():
        print('processing ' + ticker)
        map_of_pool_jsons[ticker]['live_stake'] = pool_json['epochs'][len(pool_json['epochs']) - 1]['pool_stake']
        map_of_pool_jsons[ticker]['total_stake'] = pool_json['epochs'][len(pool_json['epochs']) - 1]['total_stake']
        if map_of_pool_jsons[ticker]['live_stake'] > 0:
            map_of_pool_jsons[ticker]['underappreciated'] = map_of_pool_jsons[ticker]['cumulative_diff'] * len(map_of_pool_jsons[ticker]['epochs']) / (map_of_pool_jsons[ticker]['live_stake'] / map_of_pool_jsons[ticker]['total_stake'])
            pools.append(map_of_pool_jsons[ticker])

    performers = []
    sorted_by_underappreciated_performance = sorted(pools, key=lambda d: d['underappreciated'], reverse=True)
    rank = 0
    for pool in sorted_by_underappreciated_performance:
        if rank < 10:
            if pool['live_stake'] > (100000 * 1000000):
                if pool['cumulative_actual_blocks'] > 5:
                    current_performer = {}
                    rank += 1
                    current_performer['rank'] = rank
                    current_performer['ticker'] = pool['ticker']
                    performers.append(current_performer)

    return render_template('ranking.html', pools=performers)

@app.route("/data/<pool_ticker>.json")
def get_pool_epochs(pool_ticker):
    return map_of_pool_jsons[pool_ticker.upper()]


