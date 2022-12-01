# cardaviz.py
import psycopg2
from psycopg2.extras import RealDictCursor
import simplejson as json
from simplejson import JSONEncoder
from simplejson import JSONDecoder
from config import config
from flask import Flask, render_template
from decimal import Decimal, getcontext
from os.path import exists
import urllib.request
import os

app = Flask(__name__)
app.json_encoder = JSONEncoder
app.json_decoder = JSONDecoder


class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"


@app.route("/")
def get_landing_page():
    return "cardaviz"


@app.route("/refresh")
def quick_refresh():
    directory = 'data'
    for filename in os.listdir(directory):
        pool_file = os.path.join(directory, filename)
        if os.path.isfile(pool_file):
            print(pool_file)
            tickers_json = json.load(open('static/tickers.json'))
            pool_json = json.load(open(pool_file))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                pool_id = tickers_json[pool_ticker]
                refresh_last_epoch(pool_json, pool_id)
    return "done"

@app.route("/recalc")
def recalculate_pool():
    directory = 'data'
    for filename in os.listdir(directory):
        pool_file = os.path.join(directory, filename)
        if os.path.isfile(pool_file):
            print(pool_file)
            tickers_json = json.load(open('static/tickers.json'))
            pool_json = json.load(open(pool_file))
            pool_ticker = pool_json['ticker']
            if pool_ticker in tickers_json:
                pool_id = tickers_json[pool_ticker]
                recalculate_pool(pool_json)
    return "done"

def recalculate_pool(pool_json):
    pool_ticker = pool_json['ticker']

    print("recalculating " + pool_ticker)

    cumulative_diff = 0
    cumulative_expected_blocks = 0
    cumulative_actual_blocks = 0
    max_cumulative_diff = 0
    max_positive_cumulative_diff = 0
    max_negative_cumulative_diff = 0
    max_actual_blocks = 0
    max_expected_blocks = 0
    max_epoch_blocks= 0
    pool_json['max_epoch_blocks'] = 0

    for epoch in pool_json['epochs']:
        cumulative_expected_blocks += epoch['expected']
        epoch['cumulative_expected_blocks'] = cumulative_expected_blocks
        cumulative_actual_blocks += epoch['actual']
        epoch['cumulative_actual_blocks'] = cumulative_actual_blocks
        epoch['epoch_diff'] = epoch['actual'] - epoch['expected']
        cumulative_diff += epoch['epoch_diff']
        epoch['epoch_cumulative_diff'] = cumulative_diff

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

    ticker_json_file_name = 'data/' + pool_ticker.upper() + '.json'
    print("dumping pool to json file: " + ticker_json_file_name)
    try:
        with open(ticker_json_file_name, 'w') as outfile:
            json.dump(pool_json, outfile, indent=4, use_decimal=True)
        print("done writing to json file: " + ticker_json_file_name)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))

    return json.dumps(pool_json, indent=4, use_decimal=True)

@app.route("/pools/<pool_id>")
def get_pool(pool_id):
    return render_template('perfchart.html', pool_id=pool_id)


@app.route("/pools/<pool_id>/epochs")
def get_pool_epochs(pool_id):
    if len(pool_id) < 10:
        pool_json_path = "data/" + pool_id.upper() + ".json"
    else:
        metadata_url = get_pool_metadata_url(pool_id)
        opener = AppURLopener()
        print(metadata_url)
        metadata_json = json.load(opener.open(metadata_url))
        pool_ticker = metadata_json['ticker']
        pool_json_path = "data/" + pool_ticker.upper() + ".json"
        if not exists(pool_json_path):
            get_pool_epochs_from_database(str(pool_id), str(pool_ticker))
    return open(pool_json_path, "r").read()


def get_pool_epochs_from_database(pool_id):
    metadata_url = get_pool_metadata_url(pool_id)
    opener = AppURLopener()
    print(metadata_url)
    metadata_json = json.load(opener.open(metadata_url))
    pool_ticker = metadata_json['ticker']
    return get_pool_epochs_from_database(pool_id, pool_ticker)


def refresh_last_epoch(pool_json, pool_id):
    total_stake_json = json.load(open('static/total_stake.json'))
    pool_ticker = pool_json['ticker']
    latest_epoch = get_latest_epoch()

    conn = None
    try:
        print("fetching pool blocks for latest epoch")
        params = config()
        conn = psycopg2.connect(**params)
        blocks_cursor = conn.cursor(cursor_factory=RealDictCursor)
        blocks_query = """ SELECT count(block.block_no), block.epoch_no, pool_hash.view
                    FROM block 
                    INNER JOIN slot_leader ON block.slot_leader_id = slot_leader.id
                    INNER JOIN pool_hash ON slot_leader.pool_hash_id = pool_hash.id
                    WHERE pool_hash.view = \'""" + pool_id + "\' and epoch_no = \'" + str(latest_epoch) + """\'
                    GROUP BY block.epoch_no, pool_hash.view;"""
        print(blocks_query)
        blocks_cursor.execute(blocks_query)
        blocks_query_results = blocks_cursor.fetchall()
        print(str(blocks_query_results))
        blocks_cursor.close()

        print("fetching pool stake for all epochs")
        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = """SELECT pool_hash.view, epoch_no, sum (amount) as stake 
                        FROM epoch_stake
                        INNER JOIN pool_hash on epoch_stake.pool_id = pool_hash.id
                        WHERE pool_hash.view = \'""" + pool_id + "\' and epoch_no = \'" + str(latest_epoch) + """\'
	                    GROUP BY pool_hash.view, epoch_no
	                    ORDER BY epoch_no;"""
        print(stake_query)
        stake_cursor.execute(stake_query)
        stake_query_results = stake_cursor.fetchall()
        print(str(stake_query_results))
        stake_cursor.close()

        already_has_latest_epoch = False
        latest_epoch_element = {"epoch": latest_epoch, "expected": 0, "actual": 0}
        for json_epoch in pool_json['epochs']:
            if str(json_epoch['epoch']) == str(latest_epoch):
                latest_epoch_element = json_epoch
                already_has_latest_epoch = True

        latest_epoch_element["pool_stake"] = stake_query_results[0]['stake']

        if str(latest_epoch) in total_stake_json:
            total_stake = Decimal(total_stake_json[str(latest_epoch)])
        else:
            total_stake = Decimal(getTotalStakeForEpoch(latest_epoch))
            total_stake_json[str(latest_epoch)] = total_stake
        latest_epoch_element["total_stake"] = total_stake
        latest_epoch_element["expected"] = getExpectedEpochBlocksForPool(latest_epoch,
                                                                         latest_epoch_element["pool_stake"],
                                                                         total_stake)

        slot_coefficient = 0.05
        decentralisation_coefficient = 0

        # 5 * 24 * 60 * 60 = 432000
        print("expected")
        latest_epoch_element["expected"] = Decimal(latest_epoch_element["pool_stake"]) / Decimal(total_stake) * Decimal(
            432000) * Decimal(slot_coefficient) * Decimal((1 - decentralisation_coefficient))
        print("decentralisation_coefficient")
        latest_epoch_element["decentralisation_coefficient"] = decentralisation_coefficient
        print("slot_coefficient")
        latest_epoch_element["slot_coefficient"] = slot_coefficient
        print("actual")
        print(str(blocks_query_results))
        if len(blocks_query_results) > 0:
            latest_epoch_element["actual"] = blocks_query_results[0]['count']
        else:
            latest_epoch_element["actual"] = 0

        if not already_has_latest_epoch:
            print("adding epoch " + str(latest_epoch))
            pool_json['epochs'].append(latest_epoch_element)
        else:
            print("already has epoch " + str(latest_epoch))
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


def get_pool_epochs_from_database(pool_id, pool_ticker):
    total_stake_json = json.load(open('static/total_stake.json'))

    return_array = []
    conn = None
    try:
        print("fetching pool blocks for all epochs")
        params = config()
        conn = psycopg2.connect(**params)
        blocks_cursor = conn.cursor(cursor_factory=RealDictCursor)
        blocks_query = """ SELECT count(block.block_no), block.epoch_no, pool_hash.view
                    FROM block 
                    INNER JOIN slot_leader ON block.slot_leader_id = slot_leader.id
                    INNER JOIN pool_hash ON slot_leader.pool_hash_id = pool_hash.id
                    WHERE pool_hash.view = \'""" + pool_id + """\'
                    GROUP BY block.epoch_no, pool_hash.view;"""
        blocks_cursor.execute(blocks_query)
        blocks_query_results = blocks_cursor.fetchall()
        blocks_cursor.close()

        print("fetching pool stake for all epochs")
        stake_cursor = conn.cursor(cursor_factory=RealDictCursor)
        stake_query = """SELECT pool_hash.view, epoch_no, sum (amount) as stake 
                        FROM epoch_stake
                        INNER JOIN pool_hash on epoch_stake.pool_id = pool_hash.id
                        WHERE pool_hash.view = \'""" + pool_id + """\'
	                    GROUP BY pool_hash.view, epoch_no
	                    ORDER BY epoch_no;"""
        stake_cursor.execute(stake_query)
        stake_query_results = stake_cursor.fetchall()
        stake_cursor.close()

        first_pool_epoch = get_first_pool_epoch(pool_id)
        latest_epoch = get_latest_epoch()
        for epoch in range(first_pool_epoch, latest_epoch):
            epoch_stake = 0
            epoch_element = {"epoch": epoch, "expected": 0, "actual": 0}
            for row in stake_query_results:
                if row['epoch_no'] == epoch:
                    epoch_stake = row['stake']
            epoch_element["pool_stake"] = epoch_stake
            if str(epoch) in total_stake_json:
                total_stake = Decimal(total_stake_json[str(epoch)])
            else:
                total_stake = Decimal(getTotalStakeForEpoch(epoch))
                total_stake_json[str(epoch)] = total_stake
            epoch_element["total_stake"] = total_stake

            getcontext().prec = 6
            epoch_element["expected"] = getExpectedEpochBlocksForPool(epoch, epoch_stake, total_stake)

            slot_coefficient = 0.05
            decentralisation_coefficient = 0
            decentralisation_data = json.load(open('static/decentralisation.json'))
            if str(epoch) in decentralisation_data:
                decentralisation_coefficient = decentralisation_data[str(epoch)]

            print("epoch " + str(epoch) + " decentralisation_coefficient " + str(
                decentralisation_coefficient) + " total_stake [" + str(total_stake) + "] pool stake [" + str(
                epoch_stake) + "]")

            # 5 * 24 * 60 * 60 = 432000
            epoch_element["expected"] = Decimal(epoch_stake) / Decimal(total_stake) * Decimal(432000) * Decimal(
                slot_coefficient) * Decimal((1 - decentralisation_coefficient))
            epoch_element["decentralisation_coefficient"] = decentralisation_coefficient
            epoch_element["slot_coefficient"] = slot_coefficient

            for row in blocks_query_results:
                if row['epoch_no'] == epoch:
                    epoch_element["actual"] = row['count']
            return_array.append(epoch_element)

    except (Exception, psycopg2.DatabaseError) as error:
        return "Error: " + str(error)
    finally:
        if conn is not None:
            conn.close()
    print("dumping total_stake_json to static/total_stake.json")
    with open('static/total_stake.json', 'w') as outfile:
        json.dump(total_stake_json, outfile, indent=4, use_decimal=True)

    pool_data = {}
    pool_data['ticker'] = pool_ticker
    pool_data['epochs'] = return_array
    epoch_json = json.dumps(return_array, indent=4, use_decimal=True)
    print("dumping pool to json: " + pool_ticker)
    try:
        with open('data/' + pool_ticker.upper() + '.json', 'w') as outfile:
            json.dump(pool_data, outfile, indent=4, use_decimal=True)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: " + str(error))

    return epoch_json

@app.route("/pools/refresh")
def get_all_pools():
    tickers_json = json.load(open('static/tickers.json'))
    for (pool_ticker, pool_id) in tickers_json.items():
        print("Processing ticker: " + str(pool_ticker))
        pool_json_path = "static/" + pool_ticker.upper() + ".json"
        if not exists(pool_json_path):
            get_pool_epochs_from_database(str(pool_id), str(pool_ticker))
        else:
            print("already have json file - skipping")
    return "done"


@app.route("/tickers/refresh")
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


def getExpectedEpochBlocksForPool(epoch, epoch_stake, total_stake):
    decentralisation_coefficient = 0
    decentralisation_data = json.load(open('static/decentralisation.json'))
    if str(epoch) in decentralisation_data:
        decentralisation_coefficient = decentralisation_data[str(epoch)]

    print("epoch " + str(epoch) + " decentralisation_coefficient " + str(
        decentralisation_coefficient) + " total_stake [" + str(total_stake) + "] pool stake [" + str(epoch_stake) + "]")

    # 5 * 24 * 60 * 60 * Decimal(slot_coefficient) = 21600
    return Decimal(epoch_stake) / Decimal(total_stake) * 21600 * Decimal((1 - decentralisation_coefficient))


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
