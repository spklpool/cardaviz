import os
import time
import signal
import logging
import simplejson as json
from flask import Flask, render_template
from thread_safe_objects import ThreadSafeDictOfPoolJson
from ranking_evaluator import evaluate_ranking
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from background_thread import UpdateThread, MissingEpochsThread
from treasury import get_treasury_withdrawals_from_database, get_treasury_withdrawal_details_from_database, \
                     get_votes_for_gov_action_from_database, get_reserves_from_database, get_pots_from_database
from voting import get_drep_votes_from_database, get_pool_votes_from_database, get_vote_timeline_for_pool


#data_folder = '/var/www/html/mainnet_data/'
data_folder = '/app/cardaviz/data/mainnet_data/'

try:
    os.mkdir(data_folder)
except FileExistsError:
    print(f"Directory '{data_folder}' already exists. Moving on.")
except PermissionError:
    print(f"Permission denied: Unable to create '{data_folder}'.")
except Exception as e:
    print(f"An error occurred: {e}")

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

map_of_pool_jsons = ThreadSafeDictOfPoolJson()


#all_files = os.listdir(data_folder)
#for filename in all_files:
tickers_json = json.load(open('static/mainnet_tickers.json'))
for ticker in tickers_json:
    pool_id = tickers_json[ticker]
    pool_file = os.path.join(data_folder, pool_id + '.json')
    if os.path.isfile(pool_file):
        logging.info(f'loading: ' + pool_file)
        try:
            pool_json = json.load(open(pool_file))
            map_of_pool_jsons[pool_json['ticker']] = pool_json
        except:
            logging.info(f'exception loading json')

app = Flask(__name__)
update_thread = UpdateThread(map_of_pool_jsons)
missing_epochs_thread = MissingEpochsThread(map_of_pool_jsons)
update_thread.start()
missing_epochs_thread.start()



original_handler = signal.getsignal(signal.SIGINT)


def sigint_handler(signum, frame):
    update_thread.stop()
    if update_thread.is_alive():
        update_thread.join()
    original_handler(signum, frame)


try:
    signal.signal(signal.SIGINT, sigint_handler)
except ValueError as e:
    logging.error(f'{e}. Continuing execution...')

event_handler = DataFileChangedHandler()
observer = Observer()
observer.schedule(event_handler, path=data_folder, recursive=False)
observer.start()

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


@app.route("/pools/<pool_id>")
def get_pool(pool_id):
    return render_template('perfchart.html', pool_id=pool_id)


@app.route("/")
def get_pool_search():
    return render_template('pool_search.html')


@app.route("/ranking/<ranking_name>")
def get_ranking(ranking_name):
    ranking = evaluate_ranking(map_of_pool_jsons, ranking_name, 10)
    for pool in ranking['results']:
        print(pool['ticker'])
    return render_template('ranking.html', ranking=ranking)


@app.route("/data/<pool_ticker>.json")
def get_pool_epochs(pool_ticker):
    return map_of_pool_jsons[pool_ticker.upper()]


@app.route("/treasury_withdrawals")
def get_treasury_withdrawals():
    return get_treasury_withdrawals_from_database()


@app.route("/voting/<voter_id>")
def get_drep(voter_id):
    return render_template('voting.html', voter_id=voter_id)


@app.route("/drep_votes/<drep_id>")
def get_drep_votes(drep_id):
    return get_drep_votes_from_database(drep_id)


@app.route("/pool_votes/<pool_id>")
def get_pool_votes(pool_id):
    return get_vote_timeline_for_pool(pool_id)


@app.route("/treasury")
def get_treasury():
    return render_template('treasury.html')

