from time import sleep
import simplejson as json
import os
from update_library import get_missing_epochs, reorder_pool, refresh_epoch, recalculate_pool, get_first_pool_epoch, get_latest_epoch, data_folder, process_pool


def full_update():
    tickers_json = json.load(open('static/tickers.json'))
    for ticker in tickers_json:
        process_pool(ticker)
    return "done"

def quick_refresh():
    latest_epoch = get_latest_epoch()
    for filename in os.listdir(data_folder):
        pool_file = os.path.join(data_folder, filename)
        if os.path.isfile(pool_file):
            print(pool_file)
            tickers_json = json.load(open('static/tickers.json'))
            pool_json = json.load(open(pool_file))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                pool_id = tickers_json[pool_ticker]
                refresh_epoch(pool_json, pool_id, latest_epoch)
    return "done"


def recalculate_all_pools():
    for filename in os.listdir(data_folder):
        pool_file = os.path.join(data_folder, filename)
        if os.path.isfile(pool_file):
            print(pool_file)
            tickers_json = json.load(open('static/tickers.json'))
            pool_json = json.load(open(pool_file))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                recalculate_pool(pool_json)
    return "done"

def refresh_all_pools_for_epoch(epoch, sleep_seconds):
    print("updating " + str(epoch))
    current_count = 0
    all_files = os.listdir(data_folder)
    all_files = [os.path.join(data_folder, f) for f in all_files]
    all_files.sort(key=lambda x: os.path.getmtime(x))
    for filename in all_files:
        current_count += 1
        if os.path.isfile(filename):
            print("updating " + str(current_count) + " of " + str(len(all_files)) + " - " + filename)
            tickers_json = json.load(open('static/tickers.json'))
            pool_json = json.load(open(filename))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                pool_id = tickers_json[pool_ticker]
                refresh_epoch(pool_json, pool_id, epoch)
                recalculate_pool(pool_json)
                reorder_pool(pool_json)
                with open(data_folder + '/' + pool_ticker.upper() + '.json', 'w') as outfile:
                    json.dump(pool_json, outfile, indent=4, use_decimal=True)
                sleep(sleep_seconds)
    return "done"

full_update()
#process_pool('SPKL')
#refresh_all_pools_for_epoch(452,1)
#add_all_epochs()
