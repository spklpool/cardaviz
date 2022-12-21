import sys
import subprocess
import traceback
from time import sleep
import simplejson as json
from datetime import datetime
from config import config
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal, getcontext
import urllib.request
import os

data_folder = '/var/www/html/data'

class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"


def open_url(url):
    from urllib.request import urlopen, Request
    return urlopen(Request(url, headers={'User-Agent': 'Mozilla'}))

#TODO: reimplement a method to regenerate an entire pool json, which will need this.
def get_first_pool_epoch(pool_id):
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT min(active_epoch_no) as first_epoch
                    FROM pool_update 
                    INNER JOIN pool_hash ON pool_update.hash_id = pool_hash.id
                    WHERE pool_hash.view = \'""" + pool_id + "\';"
        cursor.execute(query)
        result = cursor.fetchall()
        return_value = result[0]['first_epoch']
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return return_value


def get_latest_epoch():
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT MAX(NO) as latest_epoch FROM epoch;"
        cursor.execute(query)
        result = cursor.fetchall()
        return_value = result[0]['latest_epoch']
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return return_value

def get_pool_epochs_from_database(pool_id):
    metadata_url = get_pool_metadata_url(pool_id)
    opener = AppURLopener()
    print(metadata_url)
    metadata_json = json.load(opener.open(metadata_url))
    pool_ticker = metadata_json['ticker']
    return get_pool_epochs_from_database(pool_id, pool_ticker)

def getExpectedEpochBlocksForPool(epoch, epoch_stake, total_stake):
    decentralisation_coefficient = 0
    decentralisation_data = json.load(open('static/decentralisation.json'))
    if str(epoch) in decentralisation_data:
        decentralisation_coefficient = decentralisation_data[str(epoch)]

    print("epoch " + str(epoch) + " decentralisation_coefficient " + str(
        decentralisation_coefficient) + " total_stake [" + str(total_stake) + "] pool stake [" + str(epoch_stake) + "]")

    # 5 * 24 * 60 * 60 * Decimal(slot_coefficient) = 21600
    return Decimal(epoch_stake) / Decimal(total_stake) * 21600 * Decimal((1 - decentralisation_coefficient))


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

def refresh_epoch(pool_json, pool_id, epoch_to_update):
    total_stake_json = json.load(open('static/total_stake.json'))
    pool_ticker = pool_json['ticker']

    conn = None
    try:
        print("fetching pool blocks for epoch " + str(epoch_to_update))
        params = config()
        conn = psycopg2.connect(**params)
        blocks_cursor = conn.cursor(cursor_factory=RealDictCursor)
        blocks_query = """ SELECT count(block.block_no), block.epoch_no, pool_hash.view
                    FROM block 
                    INNER JOIN slot_leader ON block.slot_leader_id = slot_leader.id
                    INNER JOIN pool_hash ON slot_leader.pool_hash_id = pool_hash.id
                    WHERE pool_hash.view = \'""" + pool_id + "\' and epoch_no = \'" + str(epoch_to_update) + """\'
                    GROUP BY block.epoch_no, pool_hash.view;"""
        blocks_cursor.execute(blocks_query)
        blocks_query_results = blocks_cursor.fetchall()
        blocks_cursor.close()

        print("fetching pool stake for epoch " + str(epoch_to_update))
        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = """SELECT pool_hash.view, epoch_no, sum (amount) as stake 
                        FROM epoch_stake
                        INNER JOIN pool_hash on epoch_stake.pool_id = pool_hash.id
                        WHERE pool_hash.view = \'""" + pool_id + "\' and epoch_no = \'" + str(epoch_to_update) + """\'
	                    GROUP BY pool_hash.view, epoch_no
	                    ORDER BY epoch_no;"""
        stake_cursor.execute(stake_query)
        stake_query_results = stake_cursor.fetchall()
        stake_cursor.close()

        already_has_latest_epoch = False
        epoch_element = {"epoch": epoch_to_update, "expected": 0, "actual": 0}
        for json_epoch in pool_json['epochs']:
            if str(json_epoch['epoch']) == str(epoch_to_update):
                epoch_element = json_epoch
                already_has_latest_epoch = True

        epoch_element["pool_stake"] = stake_query_results[0]['stake']

        if str(epoch_to_update) in total_stake_json:
            total_stake = Decimal(total_stake_json[str(epoch_to_update)])
        else:
            total_stake = Decimal(getTotalStakeForEpoch(epoch_to_update))
            total_stake_json[str(epoch_to_update)] = total_stake
        epoch_element["total_stake"] = total_stake

        slot_coefficient = 0.05
        decentralisation_coefficient = 0

        getcontext().prec = 6

        # 5 * 24 * 60 * 60 = 432000
        epoch_element["expected"] = Decimal(epoch_element["pool_stake"]) / Decimal(total_stake) * Decimal(
            432000) * Decimal(slot_coefficient) * Decimal((1 - decentralisation_coefficient))
        epoch_element["decentralisation_coefficient"] = decentralisation_coefficient
        epoch_element["slot_coefficient"] = slot_coefficient
        if len(blocks_query_results) > 0:
            epoch_element["actual"] = blocks_query_results[0]['count']
        else:
            epoch_element["actual"] = 0

        if not already_has_latest_epoch:
            print("adding epoch " + str(epoch_to_update))
            pool_json['epochs'].append(epoch_element)
        else:
            print("already has epoch " + str(epoch_to_update))
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))
    finally:
        if conn is not None:
            conn.close()

    ticker_json_file_name = data_folder + '/' + pool_ticker.upper() + '.json'
    print("dumping pool to json file: " + ticker_json_file_name)
    try:
        with open(ticker_json_file_name, 'w') as outfile:
            json.dump(pool_json, outfile, indent=4, use_decimal=True)
        print("done writing to json file: " + ticker_json_file_name)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))

    recalculated_pool_json = recalculate_pool(pool_json)

    return json.dumps(recalculated_pool_json, indent=4, use_decimal=True)


def getTotalStakeForEpoch(epoch):
    epoch_stake = Decimal('0')
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = "SELECT epoch_no, sum (amount) AS stake FROM epoch_stake WHERE epoch_no = " + str(
            epoch) + " GROUP BY epoch_no;"
        stake_cursor.execute(stake_query)
        stake_query_results = stake_cursor.fetchall()
        for row in stake_query_results:
            if row['epoch_no'] == epoch:
                epoch_stake = row['stake']
        stake_cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return "Error: " + str(error)
    finally:
        if conn is not None:
            conn.close()

    return epoch_stake


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


def recalculate_pool(pool_json):
    pool_ticker = pool_json['ticker']

    print("recalculating " + pool_ticker)

    cumulative_diff = Decimal(0)
    cumulative_expected_blocks = Decimal(0)
    cumulative_actual_blocks = Decimal(0)
    max_cumulative_diff = Decimal(0)
    max_positive_cumulative_diff = Decimal(0)
    max_negative_cumulative_diff = Decimal(0)
    max_actual_blocks = Decimal(0)
    max_expected_blocks = Decimal(0)
    max_epoch_blocks= Decimal(0)
    pool_json['max_epoch_blocks'] =Decimal(0)

    for epoch in pool_json['epochs']:
        try:
            cumulative_expected_blocks += Decimal(epoch['expected'])
            epoch['cumulative_expected_blocks'] = cumulative_expected_blocks
            cumulative_actual_blocks += Decimal(epoch['actual'])
            epoch['cumulative_actual_blocks'] = cumulative_actual_blocks
            epoch['epoch_diff'] = Decimal(epoch['actual']) - Decimal(epoch['expected'])
            cumulative_diff += Decimal(epoch['epoch_diff'])
            epoch['epoch_cumulative_diff'] = cumulative_diff
        except (Exception) as error:
            print("Error: " + str(error))
            print(traceback.format_exc())


        if (abs(cumulative_diff) > abs(max_cumulative_diff)):
            max_cumulative_diff = abs(cumulative_diff)
            if (cumulative_diff > 0):
                max_positive_cumulative_diff = max_cumulative_diff
            else:
                max_negative_cumulative_diff = max_cumulative_diff

        if epoch['actual'] > max_actual_blocks:
            max_actual_blocks = epoch['actual']

        if epoch['expected'] > max_expected_blocks:
            max_expected_blocks = epoch['expected']

        if max_actual_blocks > max_epoch_blocks:
            max_epoch_blocks = max_actual_blocks

        if max_expected_blocks > max_epoch_blocks:
            max_epoch_blocks = max_expected_blocks

    pool_json['max_positive_diff'] = max_positive_cumulative_diff
    pool_json['max_negative_diff'] = max_negative_cumulative_diff
    pool_json['max_cumulative_diff'] = max_cumulative_diff
    pool_json['cumulative_diff'] = cumulative_diff
    pool_json['cumulative_expected_blocks'] = cumulative_expected_blocks
    pool_json['cumulative_actual_blocks'] = cumulative_actual_blocks
    pool_json['max_actual_blocks'] = max_actual_blocks
    pool_json['max_expected_blocks'] = max_expected_blocks
    pool_json['max_epoch_blocks'] = max_epoch_blocks
    if pool_json['cumulative_expected_blocks'] > 0:
        pool_json['current_lifetime_luck'] = (pool_json['cumulative_actual_blocks'] / pool_json['cumulative_expected_blocks']) * 100
        pool_json['highest_lifetime_luck'] = (1 + (pool_json['max_positive_diff'] / pool_json['cumulative_expected_blocks'])) * 100
        pool_json['lowest_lifetime_luck'] = (1 - (pool_json['max_negative_diff'] / pool_json['cumulative_expected_blocks'])) * 100
    else:
        pool_json['current_lifetime_luck'] = 0
        pool_json['highest_lifetime_luck'] = 0
        pool_json['lowest_lifetime_luck'] = 0

    ticker_json_file_name = data_folder + '/' + pool_ticker.upper() + '.json'
    print("dumping pool to json file: " + ticker_json_file_name)
    try:
        with open(ticker_json_file_name, 'w') as outfile:
            json.dump(pool_json, outfile, indent=4, use_decimal=True)
        print("done writing to json file: " + ticker_json_file_name)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))

    return json.dumps(pool_json, indent=4, use_decimal=True)

def get_all_tickers():
    ticker_map = {}
    view_map = {}
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT * from pool_update 
                    INNER JOIN pool_hash ON pool_update.hash_id = pool_hash.id
                    WHERE registered_tx_id IN (
                        SELECT max(registered_tx_id) 
                        FROM pool_update group by hash_id) and not exists
                            ( select * from pool_retire where pool_retire.hash_id = pool_update.hash_id
                            and pool_retire.retiring_epoch <= (select max (epoch_no) from block)) ;"""
        cursor.execute(query)
        query_results = cursor.fetchall()
        cursor.close()

        for row in query_results:
            current_pool_view = row['view']
            print("getting metadata for pool id [" + current_pool_view + "]")
            try:
                metadata_url = get_pool_metadata_url(current_pool_view)
                print(metadata_url)
                opener = AppURLopener()
                print(metadata_url)
                metadata_json = json.load(opener.open(metadata_url))
                ticker_map[metadata_json['ticker']] = current_pool_view
                view_map[current_pool_view] = metadata_json['ticker']

            except(Exception, psycopg2.DatabaseError) as error:
                print(error)


    except (Exception, psycopg2.DatabaseError) as error:
        return "Error: " + str(error)
    finally:
        if conn is not None:
            conn.close()

    with open('static/tickers.json', 'w') as outfile:
        outfile.write(json.dumps(ticker_map, indent=4, use_decimal=True))
    with open('static/pool_tickers.json', 'w') as outfile:
        outfile.write(json.dumps(view_map, indent=4, use_decimal=True))

    return 'done'


def get_pool_metadata_url(pool_id):
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """SELECT pool_metadata_ref.id, url FROM pool_metadata_ref 
        INNER JOIN pool_hash on pool_hash.id = pool_metadata_ref.pool_id 
        WHERE pool_hash.view = \'""" + pool_id + """\'
        ORDER BY pool_metadata_ref.id DESC
        LIMIT 1;"""
        cursor.execute(query)
        results = cursor.fetchall()
        ret = results[0]['url']
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return "Error: " + str(error)
    finally:
        if conn is not None:
            conn.close()
    return ret


def refresh_all_pools_for_next_epoch():
    latest_epoch = get_latest_epoch()
    print(latest_epoch)

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


#TODO: add a method to efficiently discover new pools as part of the update
def update():
    latest_epoch = get_latest_epoch()
    updates_file_name = 'static/updates.json'
    pool_tickers_file_name = 'static/pool_tickers.json'

    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print("Current Time =", current_time)

    updates_json = json.load(open(updates_file_name))
    pool_tickers_json = json.load(open(pool_tickers_file_name))

    last_update_time = updates_json[len(updates_json)-1]['time']

    current_update = {}
    current_update['time'] = current_time
    current_update['last_time'] = last_update_time

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
            print('processing ' + str(processing_count) + ' of ' + str(len(valid_pools_needing_updates)))
            try:
                pool_json_path = data_folder + "/" + row['ticker'].upper() + ".json"
                pool_json = json.load(open(pool_json_path))
                refresh_epoch(pool_json, row['view'], latest_epoch - 1)
                refresh_epoch(pool_json, row['view'], latest_epoch)
                update_thumbnail(row['ticker'].upper())

            except (Exception) as metadata_error:
                print(metadata_error)

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))
    finally:
        if conn is not None:
            conn.close()


def update_thumbnail(pool_ticker):
    p = subprocess.Popen('node generate.js ' + pool_ticker.upper(), 120)
    p.wait()


if (len(sys.argv) > 0):
    refresh_all_pools_for_next_epoch()
else:
    while True:
        update()
        sleep(10)
