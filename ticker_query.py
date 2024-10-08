import simplejson as json
from config import config
import psycopg2
from psycopg2.extras import RealDictCursor


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
            print(row['ticker'])

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


get_all_tickers('mainnet')
