import sys

from update_library import refresh_epoch, data_folder
import simplejson as json


def update_pool_for_epoch(pool_ticker, epoch):
    pool_json = json.load(open(data_folder + '/' + pool_ticker.upper() + '.json'))
    tickers_json = json.load(open('static/tickers.json'))
    if pool_ticker in tickers_json:
        pool_id = tickers_json[pool_ticker]
        refresh_epoch(pool_json, pool_id, epoch)
    return "done"

print('updating ' + sys.argv[1] + ' for epoch ' + str(sys.argv[2]))
update_pool_for_epoch(sys.argv[1], sys.argv[2])
