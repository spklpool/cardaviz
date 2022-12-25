from time import sleep
import simplejson as json
from datetime import datetime
from config import config
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from update_library import refresh_epoch, recalculate_pool, get_first_pool_epoch, get_latest_epoch, data_folder


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
                sleep(sleep_seconds)
    return "done"


def update():
    latest_epoch = get_latest_epoch()
    updates_file_name = 'static/updates.json'
    pool_tickers_file_name = 'static/pool_tickers.json'

    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print("Current Time =", current_time)

    updates_json = json.load(open(updates_file_name))
    pool_tickers_json = json.load(open(pool_tickers_file_name))

    last_update_time = updates_json[len(updates_json)-1]['time']

    current_update = {'time': current_time, 'last_time': last_update_time}

    conn = None
    try:
        print("fetching pools with blocks since " + last_update_time)
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT DISTINCT pool_hash.view
                    FROM block 
                    INNER JOIN slot_leader ON slot_leader.id = block.slot_leader_id
                    INNER JOIN pool_hash ON pool_hash.id = slot_leader.pool_hash_id
                    WHERE TIME > \'""" + last_update_time + "\' ;"""
        cursor.execute(query)
        query_results = cursor.fetchall()
        cursor.close()

        valid_pools_needing_updates = []
        for row in query_results:
            if row['view'] in pool_tickers_json:
                current_pool_needing_update = {}
                current_pool_needing_update['view'] = row['view']
                current_pool_needing_update['ticker'] = pool_tickers_json[row['view']]
                valid_pools_needing_updates.append(current_pool_needing_update)

        if len(valid_pools_needing_updates) > 0:
            current_update['updates'] = len(valid_pools_needing_updates)
            updates_json.append(current_update)
            with open(updates_file_name, 'w') as outfile:
                json.dump(updates_json, outfile, indent=4, use_decimal=True)
        else:
            print('nothing to update - waiting a few seconds')

        print('out of ' + str(len(query_results)) + ' keeping ' + str(len(valid_pools_needing_updates)) + ' that have working tickers')

        processing_count = 0
        for row in valid_pools_needing_updates:
            processing_count += 1
            print('processing ' + str(processing_count) + ' of ' + str(len(valid_pools_needing_updates)) + ' - ' + row['ticker'].upper())
            try:
                pool_json_path = data_folder + "/" + row['ticker'].upper() + ".json"
                pool_json = json.load(open(pool_json_path))
                refresh_epoch(pool_json, row['view'], latest_epoch - 1)
                refresh_epoch(pool_json, row['view'], latest_epoch)

                recalculate_pool(pool_json)

                with open(data_folder + '/' + ticker.upper() + '.json', 'w') as outfile:
                    json.dump(pool_json, outfile, indent=4, use_decimal=True)

            except (Exception) as metadata_error:
                print(metadata_error)

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))
    finally:
        if conn is not None:
            conn.close()


while True:
    update()
    sleep(10)
