import traceback

import os
import psycopg2
import simplejson as json
from config import config
from psycopg2.extras import RealDictCursor
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from os.path import exists


#base_data_folder = './data'
base_data_folder = '/var/www/html'

def load_tickers_json(network='mainnet'):
        return json.load(open('static/' + network + '_tickers.json'))

def process_pool(ticker, network='mainnet'):
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    pool_id = tickers_json[ticker]
    pool_file_path = base_data_folder +  '/' + network + '_data/' + pool_id + '.json'
    print('processing file ' + pool_file_path)
    if not os.path.isfile(pool_file_path):
        first_epoch = get_first_pool_epoch(pool_id, network)
        print('first epoch is ' + str(first_epoch))
        latest_epoch = get_latest_epoch(network)
        print('latest epoch is ' + str(latest_epoch))
        pool_json = {}
        pool_json['ticker'] = ticker.upper()
        pool_json['id'] = pool_id
        pool_json['epochs'] = []
        for searched_epoch in range(first_epoch, latest_epoch + 1):
            print('updating ' + ticker + " for epoch " + str(searched_epoch))
            refresh_epoch(pool_json, pool_id, searched_epoch, network)
            recalculate_pool(pool_json)
            reorder_pool(pool_json)
            with open(pool_file_path, 'w') as outfile:
                json.dump(pool_json, outfile, indent=4, use_decimal=True)        

def get_first_pool_epoch(pool_id, network='mainnet'):
    conn = None
    try:
        params = config(network + '.ini')
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
        print(str(error))
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return return_value


def is_in_quiet_period(network='mainnet'):
    ret = True
    conn = None
    try:
        params = config(network + '.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT completed FROM epoch_stake_progress WHERE epoch_no = (SELECT MAX(NO) FROM epoch); """
        cursor.execute(query)
        result = cursor.fetchall()
        if result[0]['completed'] == True:
            ret = False
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(str(error))
    finally:
        if conn is not None:
            conn.close()

    return ret


def get_latest_epoch(network='mainnet'):
    conn = None
    try:
        #five_hours_ago = datetime.utcnow() - timedelta(hours=5)
        #date_time_threshold_string = five_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
        params = config(network + '.ini')
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


def is_epoch_state_complete(epoch):
    ret = False
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = "SELECT epoch_no, completed FROM epoch_stake_progress WHERE epoch_no = " + str(epoch)
        stake_cursor.execute(stake_query)
        stake_query_results = stake_cursor.fetchall()
        for row in stake_query_results:
            if row['epoch_no'] == epoch:
                ret = row['completed']
        stake_cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return "Error: " + str(error)
    finally:
        if conn is not None:
            conn.close()
    return ret


def get_totalStake_for_epoch(epoch, network='mainnet'):
    epoch_stake = Decimal('0')
    conn = None
    if is_epoch_state_complete(epoch) == False:
        return 0

    try:
        params = config(network + '.ini')
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


def refresh_epoch(pool_json, pool_id, epoch_to_update, network='mainnet'):
    total_stake_json = json.load(open('static/total_stake.json'))

    conn = None
    try:
        params = config(network + '.ini')
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

        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = """SELECT pool_hash.view, count(*) as delegator_count, epoch_no, sum (amount) as stake 
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

        if len(stake_query_results) > 0:
            epoch_element["delegator_count"] = stake_query_results[0]['delegator_count']
        else:
            epoch_element["delegator_count"] = 0

        if len(stake_query_results) > 0:
            epoch_element["pool_stake"] = stake_query_results[0]['stake']
        else:
            epoch_element["pool_stake"] = 0

        if str(epoch_to_update) in total_stake_json:
            total_stake = Decimal(total_stake_json[str(epoch_to_update)])
        else:
            total_stake = Decimal(get_totalStake_for_epoch(epoch_to_update, network))
            if total_stake > 0:
                total_stake_json[str(epoch_to_update)] = total_stake
                with open('static/total_stake.json', 'w') as outfile:
                    print('adding total_stake to json: ' + str(total_stake))
                    json.dump(total_stake_json, outfile, indent=4, use_decimal=True)

        epoch_element["total_stake"] = total_stake

        slot_coefficient = 0.05
        decentralisation_coefficient = 0
        decentralisation_data = json.load(open('static/decentralisation.json'))
        if str(epoch_to_update) in decentralisation_data:
            decentralisation_coefficient = decentralisation_data[str(epoch_to_update)]

        getcontext().prec = 6

        # 5 * 24 * 60 * 60 = 432000
        epoch_element["expected"] = round(Decimal(epoch_element["pool_stake"]) / Decimal(total_stake) * Decimal(
            432000) * Decimal(slot_coefficient) * Decimal((1 - decentralisation_coefficient)), 2)
        epoch_element["decentralisation_coefficient"] = decentralisation_coefficient
        epoch_element["slot_coefficient"] = slot_coefficient
        if len(blocks_query_results) > 0:
            epoch_element["actual"] = blocks_query_results[0]['count']
        else:
            epoch_element["actual"] = 0

        if not already_has_latest_epoch:
            pool_json['epochs'].append(epoch_element)

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))
        traceback.print_exc()

    finally:
        if conn is not None:
            conn.close()


def getExpectedEpochBlocksForPool(epoch, epoch_stake, total_stake):
    decentralisation_coefficient = 0
    decentralisation_data = json.load(open('static/decentralisation.json'))
    if str(epoch) in decentralisation_data:
        decentralisation_coefficient = decentralisation_data[str(epoch)]

    print("epoch " + str(epoch) + " decentralisation_coefficient " + str(
        decentralisation_coefficient) + " total_stake [" + str(total_stake) + "] pool stake [" + str(epoch_stake) + "]")

    # 5 * 24 * 60 * 60 * Decimal(slot_coefficient) = 21600
    return Decimal(epoch_stake) / Decimal(total_stake) * 21600 * Decimal((1 - decentralisation_coefficient))


def list_missing_pools(network='mainnet'):
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    for ticker in tickers_json:
        pool_id = tickers_json[ticker]
        if not exists(base_data_folder + '/' + network + '_data/' + pool_id + '.json'):
            print(pool_id + ' ' + ticker)

def get_missing_epochs(pool_json, network='mainnet'):
    ret = []
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    pool_id = tickers_json[pool_json['ticker']]
    first_epoch = get_first_pool_epoch(pool_id)
    latest_epoch = get_latest_epoch()
    for searched_epoch in range(first_epoch, latest_epoch + 1):
        contains_epoch = False
        for target_epoch_index in range(0, len(pool_json['epochs'])):
            if pool_json['epochs'][target_epoch_index]['epoch'] == searched_epoch:
                if 'delegator_count' in pool_json['epochs'][target_epoch_index]:
                    contains_epoch = True
                    break
        if not contains_epoch:
            ret.append(searched_epoch)
    return ret

def get_missing_epochs_bak(pool_json, network='mainnet'):
    ret = []
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    pool_id = tickers_json[pool_json['ticker']]
    first_epoch = get_first_pool_epoch(pool_id)
    latest_epoch = get_latest_epoch()
    for searched_epoch in range(first_epoch, latest_epoch + 1):
        contains_epoch = False
        for target_epoch_index in range(0, len(pool_json['epochs'])):
            if pool_json['epochs'][target_epoch_index]['epoch'] == searched_epoch:
                contains_epoch = True
                break
        if not contains_epoch:
            ret.append(searched_epoch)
    return ret

def get_all_tickers(network='mainnet'):
    ticker_map = {}
    view_map = {}
    conn = None
    try:
        params = config(network + '.ini', 'postgresql')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT pool_hash.view, off_chain_pool_data.ticker_name as ticker
                    FROM pool_hash
                    INNER JOIN off_chain_pool_data ON off_chain_pool_data.pool_id = pool_hash.id
                    INNER JOIN pool_update ON pool_update.hash_id = pool_hash.id
                    WHERE registered_tx_id IN (
                        SELECT max(registered_tx_id)
                        FROM pool_update
                        GROUP BY hash_id) and not exists
                          ( select * from pool_retire where pool_retire.hash_id = pool_update.hash_id
                          and pool_retire.retiring_epoch <= (select max (epoch_no) from block))
                    AND off_chain_pool_data.id IN (SELECT MAX(id) FROM off_chain_pool_data GROUP BY off_chain_pool_data.pool_id)
                    ORDER BY ticker_name"""
        cursor.execute(query)
        query_results = cursor.fetchall()
        cursor.close()

        for row in query_results:
            ticker_map[row['ticker']] = row['view']
            view_map[row['view']] = row['ticker']

    except (Exception, psycopg2.DatabaseError) as error:
        print(str(error))
        return "Error: " + str(error)
    finally:
        if conn is not None:
            conn.close()

    with open('static/' + network + '_tickers.json', 'w') as outfile:
        outfile.write(json.dumps(ticker_map, indent=4, use_decimal=True))
    with open('static/' + network + '_pool_tickers.json', 'w') as outfile:
        outfile.write(json.dumps(view_map, indent=4, use_decimal=True))

    return 'done'

def reset_tickers(map_of_pool_jsons, network='mainnet'):
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    for pool_ticker in tickers_json:
        pool_id = tickers_json[pool_ticker]
        pool_file_path = '/var/www/html/mainnet_data/' + pool_id + '.json'
        if os.path.exists(pool_file_path):
            pool_json = json.load(open(pool_file_path))
            if pool_json['ticker'] != pool_ticker:
                print('resetting ticker for pool: ' + pool_ticker + ' ' + pool_id)
                pool_json['ticker'] = pool_ticker
                pool_file_path = base_data_folder +  '/' + network + '_data/' + pool_id + '.json'
                with open(pool_file_path, 'w') as outfile:
                    json.dump(pool_json, outfile, indent=4, use_decimal=True)
    return "done"

def reorder_pool(pool_json):
    pool_ticker = pool_json['ticker']
    print("reordering " + pool_ticker)
    pool_json['epochs'] = sorted(pool_json['epochs'], key=lambda d: d['epoch'])

def add_missing_pools(network='mainnet'):
    tickers_to_update = []
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    for ticker in tickers_json:
        pool_id = tickers_json[ticker]
        if not os.path.exists(base_data_folder + '/' + network + '_data/' + pool_id + '.json'):
            tickers_to_update.append(ticker)

    latest_epoch = get_latest_epoch()
    progress_count = 0
    for ticker in tickers_to_update:
        pool_id = tickers_json[ticker]
        pool_json = {}
        pool_json['ticker'] = ticker
        pool_json['epochs'] = []
        progress_count += 1
        first_epoch = get_first_pool_epoch(tickers_json[ticker]);
        print('updating ' + str(progress_count) + ' of ' + str(len(tickers_to_update)) + ' - ' + ticker + '(' + str(first_epoch) + ',' + str(latest_epoch) + ')')
        for epoch in range(first_epoch, latest_epoch + 1):
            print('updating ' + str(progress_count) + ' of ' + str(len(tickers_to_update)) + ' - ' + ticker + ' - epoch ' + str(epoch))
            refresh_epoch(pool_json, tickers_json[ticker], epoch)

        recalculate_pool(pool_json)

        with open(base_data_folder + '/' + network + '_data/' + pool_id + '.json', 'w') as outfile:
            json.dump(pool_json, outfile, indent=4, use_decimal=True)

def add_all_missing_epochs(map_of_pool_jsons, network='mainnet'):
    latest_epoch = get_latest_epoch()
    tickers_json = json.load(open('static/' + network + '_tickers.json'))
    current_count = 0
    pool_keys = map_of_pool_jsons.keys()
    total_count = len(pool_keys)
    for pool_ticker in pool_keys:
        current_count += 1
        pool_json = map_of_pool_jsons[pool_ticker]
        if pool_ticker in tickers_json:
            pool_id = tickers_json[pool_ticker]
            missing_epochs = get_missing_epochs(pool_json)
            if len(missing_epochs) > 0:
                for index in range(0, len(missing_epochs)):
                    print('adding missing epochs for pool ' + str(current_count) + ' of ' + 
                            str(total_count) + ' ' + pool_ticker + ' updating epoch ' + 
                            str(index) + ' of ' + str(len(missing_epochs)) + ' missing epochs')
                    refresh_epoch(pool_json, pool_id, missing_epochs[index])
                recalculate_pool(pool_json)
                reorder_pool(pool_json)
                pool_file_path = base_data_folder +  '/' + network + '_data/' + pool_id + '.json'
                with open(pool_file_path, 'w') as outfile:
                    json.dump(pool_json, outfile, indent=4, use_decimal=True)
            else:
                latest_epoch = get_latest_epoch()
                print('no missing epochs for pool ' + pool_ticker + ' at epoch ' + str(latest_epoch))
                
    return "done"

def recalculate_pool(pool_json):
    latest_epoch = get_latest_epoch();
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
    max_epoch_blocks = Decimal(0)
    pool_json['max_epoch_blocks'] = Decimal(0)
    blocks_in_last_ten_epochs = 0
    last_delegator_count = 0


    for epoch in pool_json['epochs']:
        try:
            if epoch['epoch'] > (latest_epoch - 10):
                blocks_in_last_ten_epochs += epoch['actual']
            cumulative_expected_blocks += Decimal(epoch['expected'])
            epoch['cumulative_expected_blocks'] = cumulative_expected_blocks
            cumulative_actual_blocks += Decimal(epoch['actual'])
            epoch['cumulative_actual_blocks'] = cumulative_actual_blocks
            epoch['epoch_diff'] = Decimal(epoch['actual']) - Decimal(epoch['expected'])
            cumulative_diff += Decimal(epoch['epoch_diff'])
            epoch['epoch_cumulative_diff'] = cumulative_diff
            last_delegator_count = epoch['delegator_count']
        except (Exception) as error:
            print("Error: " + str(error))
            traceback.print_exc()

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

    latest_pool_epoch = {}
    for epoch in pool_json['epochs']:
        if epoch['epoch'] == latest_epoch:
            latest_pool_epoch = epoch
            break

    if 'pool_stake' in latest_pool_epoch:
        pool_json['latest_epoch_pool_stake'] = latest_pool_epoch['pool_stake']
    if 'total_stake' in latest_pool_epoch:
        pool_json['latest_epoch_total_stake'] = latest_pool_epoch['total_stake']

    pool_json['last_delegator_count'] = last_delegator_count
    pool_json['blocks_in_last_ten_epochs'] = blocks_in_last_ten_epochs
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
        pool_json['current_lifetime_luck'] = round(0, 2)
        pool_json['highest_lifetime_luck'] = round(0, 2)
        pool_json['lowest_lifetime_luck'] = round(0, 2)

    print("done recalculating " + pool_ticker)
