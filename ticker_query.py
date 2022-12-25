import simplejson as json
from config import config
import psycopg2
from psycopg2.extras import RealDictCursor


def get_all_tickers():
    ticker_map = {}
    view_map = {}
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT pool_hash.view, pool_offline_data.ticker_name as ticker
                    FROM pool_hash
                    INNER JOIN pool_offline_data ON pool_offline_data.pool_id = pool_hash.id 
                    INNER JOIN pool_update ON pool_update.hash_id = pool_hash.id
                    WHERE registered_tx_id IN (
                        SELECT max(registered_tx_id) 
                        FROM pool_update 
                        GROUP BY hash_id) and not exists
                          ( select * from pool_retire where pool_retire.hash_id = pool_update.hash_id
                          and pool_retire.retiring_epoch <= (select max (epoch_no) from block))
                    ORDER BY ticker_name"""
        cursor.execute(query)
        query_results = cursor.fetchall()
        cursor.close()

        for row in query_results:
            ticker_map[row['ticker']] = row['view']
            view_map[row['view']] = row['ticker']

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


get_all_tickers()