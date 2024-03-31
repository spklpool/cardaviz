from time import sleep
import simplejson as json
import os
from os.path import exists
from update_library import get_missing_epochs, reorder_pool, refresh_epoch, recalculate_pool, get_first_pool_epoch, get_latest_epoch, process_pool, load_tickers_json, is_epoch_state_complete


def full_update(network='mainnet'):
    current_count = 0
    tickers_json = load_tickers_json(network)
    total_count = len(tickers_json)
    for ticker in tickers_json:
        print(str(current_count) + ' of ' + str(total_count) + ' ' + ticker)
        process_pool(ticker, network)
    return "done"

def add_missing_pools(network='mainnet'):
    current_count = 0
    tickers_json = load_tickers_json(network)
    total_count = len(tickers_json)
    for ticker in tickers_json:
        current_count += 1
        print(str(current_count) + ' of ' + str(total_count) + ' ' + ticker)
        pool_id = tickers_json[ticker]
        if not exists(data_folder + '/' + network + '_data/' + pool_id + '.json'):
            process_pool(ticker, network)

def quick_refresh(network='mainnet'):
    latest_epoch = get_latest_epoch()
    for filename in os.listdir(data_folder):
        pool_file = os.path.join(data_folder, filename)
        if os.path.isfile(pool_file):
            print(pool_file)
            tickers_json = load_tickers_json(network)
            pool_json = json.load(open(pool_file))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                pool_id = tickers_json[pool_ticker]
                refresh_epoch(pool_json, pool_id, latest_epoch)
    return "done"


def recalculate_all_pools(network='mainnet'):
    for filename in os.listdir(data_folder):
        pool_file = os.path.join(data_folder, filename)
        if os.path.isfile(pool_file):
            print(pool_file)
            tickers_json = load_tickers_json(network)
            pool_json = json.load(open(pool_file))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                recalculate_pool(pool_json)
    return "done"

def refresh_pool_for_epoch(ticker, epoch, sleep_seconds, network='mainnet'):
    print("updating " + str(epoch))
    tickers_json = load_tickers_json(network)
    pool_id = tickers_json[ticker]
    pool_file_path = data_folder + '/' + pool_id + '.json'
    pool_json = json.load(open(pool_file_path))
    refresh_epoch(pool_json, pool_id, epoch, network)
    recalculate_pool(pool_json)
    reorder_pool(pool_json)
    with open(pool_file_path, 'w') as outfile:
        json.dump(pool_json, outfile, indent=4, use_decimal=True)
    return "done"

def refresh_all_pools_for_epoch(epoch, sleep_seconds, network='mainnet'):
    print("updating " + str(epoch))
    current_count = 0
    all_files = os.listdir(data_folder)
    all_files = [os.path.join(data_folder, f) for f in all_files]
    all_files.sort(key=lambda x: os.path.getmtime(x))
    for filename in all_files:
        current_count += 1
        if os.path.isfile(filename):
            print("updating " + str(current_count) + " of " + str(len(all_files)) + " - " + filename)
            tickers_json = load_tickers_json(network)
            pool_json = json.load(open(filename))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                pool_id = tickers_json[pool_ticker]
                refresh_epoch(pool_json, pool_id, epoch)
                recalculate_pool(pool_json)
                reorder_pool(pool_json)
                with open(data_folder + '/' + pool_id + '.json', 'w') as outfile:
                    json.dump(pool_json, outfile, indent=4, use_decimal=True)
                sleep(sleep_seconds)
    return "done"

#network = 'sancho'
network = 'mainnet'
data_folder = '/var/www/html/' + network + '_data'
#while(True):
#    latest_epoch = get_latest_epoch()
#    if is_epoch_state_complete(latest_epoch):
#        refresh_all_pools_for_epoch(latest_epoch, 1, network)
#    refresh_all_pools_for_epoch(latest_epoch - 1, 1, network)
add_missing_pools(network)
