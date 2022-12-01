from time import sleep

import simplejson as json
from datetime import datetime
from config import config
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal, getcontext

def open_url(url):
    from urllib.request import urlopen, Request
    return urlopen(Request(url, headers={'User-Agent': 'Mozilla'}))

def getExpectedEpochBlocksForPool(epoch, epoch_stake, total_stake):
    decentralisation_coefficient = 0
    decentralisation_data = json.load(open('static/decentralisation.json'))
    if str(epoch) in decentralisation_data:
        decentralisation_coefficient = decentralisation_data[str(epoch)]

    print("epoch " + str(epoch) + " decentralisation_coefficient " + str(
        decentralisation_coefficient) + " total_stake [" + str(total_stake) + "] pool stake [" + str(epoch_stake) + "]")

    # 5 * 24 * 60 * 60 * Decimal(slot_coefficient) = 21600
    return Decimal(epoch_stake) / Decimal(total_stake) * 21600 * Decimal((1 - decentralisation_coefficient))

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

    ticker_json_file_name = 'data/' + pool_ticker.upper() + '.json'
    print("dumping pool to json file: " + ticker_json_file_name)
    try:
        with open(ticker_json_file_name, 'w') as outfile:
            json.dump(pool_json, outfile, indent=4, use_decimal=True)
        print("done writing to json file: " + ticker_json_file_name)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))

    return json.dumps(pool_json, indent=4, use_decimal=True)


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

def update():
    updates_file_name = 'static/updates.json'
    tickers_file_name = 'static/tickers.json'
    pool_tickers_file_name = 'static/pool_tickers.json'

    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print("Current Time =", current_time)

    updates_json = json.load(open(updates_file_name))
    tickers_json = json.load(open(tickers_file_name))
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
        query = """ SELECT DISTINCT pool_hash.view, pool_metadata_ref.url 
                    FROM block 
                    INNER JOIN slot_leader ON slot_leader.id = block.slot_leader_id
                    INNER JOIN pool_hash ON pool_hash.id = slot_leader.pool_hash_id
                    INNER JOIN pool_metadata_ref ON slot_leader.pool_hash_id = pool_metadata_ref.pool_id 
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
            print('nothing to update - will speep for a minute and try again')

        print('out of ' + str(len(query_results)) + ' keeping ' + str(len(valid_pools_needing_updates)) + ' that have working tickers')

        processing_count = 0
        for row in valid_pools_needing_updates:
            processing_count += 1
            print('processing ' + str(processing_count) + ' of ' + str(len(valid_pools_needing_updates)))
            try:
                pool_json_path = "data/" + row['ticker'].upper() + ".json"
                pool_json = json.load(open(pool_json_path))
                refresh_epoch(pool_json, row['view'], 379)

            except (Exception) as metadata_error:
                print(metadata_error)

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))
    finally:
        if conn is not None:
            conn.close()
    sleep(60)
    update()

update()