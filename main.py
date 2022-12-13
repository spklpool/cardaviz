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

directory = '/root/git/cardaviz/data/'
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


#TODO: add a landing page here
@app.route("/")
def get_landing_page():
    return "cardaviz"


@app.route("/pools/<pool_ticker>")
def get_pool(pool_ticker):
    return render_template('perfchart.html', pool_ticker=pool_ticker)


@app.route("/pools/<pool_ticker>/epochs")
def get_pool_epochs(pool_ticker):
    start = time.time()
    loaded_file = map_of_pool_jsons[pool_ticker.upper()]
    print(f'Time: {time.time() - start}')
    return loaded_file


