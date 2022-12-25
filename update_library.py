import traceback

import psycopg2
import simplejson as json
from config import config
from psycopg2.extras import RealDictCursor
from decimal import Decimal, getcontext


data_folder = './data'


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


def get_totalStake_for_epoch(epoch):
    epoch_stake = Decimal('0')
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = "SELECT epoch_no, sum (amount) AS stake FROM epoch_stake WHERE epoch_no = " + str(
            epoch) + " GROUP BY epoch_no;"
        print(stake_query)
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


def refresh_epoch(pool_json, pool_id, epoch_to_update):
    total_stake_json = json.load(open('static/total_stake.json'))

    conn = None
    try:
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
            print('total_stake from existing json: ' + str(total_stake))
        else:
            total_stake = Decimal(get_totalStake_for_epoch(epoch_to_update))
            if total_stake > 0:
                total_stake_json[str(epoch_to_update)] = total_stake
                with open('static/total_stake.json', 'w') as outfile:
                    print('adding total_stake to json: ' + str(total_stake))
                    json.dump(total_stake_json, outfile, indent=4, use_decimal=True)

        epoch_element["total_stake"] = total_stake

        print('total_stake: ' + str(total_stake))

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

