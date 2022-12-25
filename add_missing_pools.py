import os
import simplejson as json
from update_library import refresh_epoch, recalculate_pool, get_first_pool_epoch, get_latest_epoch, data_folder


def add_missing_pools():
    tickers_to_update = []
    tickers_json = json.load(open('static/tickers.json'))
    for ticker in tickers_json:
        if not os.path.exists(data_folder + '/' + ticker.upper() + '.json'):
            tickers_to_update.append(ticker)

    latest_epoch = get_latest_epoch()
    progress_count = 0
    for ticker in tickers_to_update:
        pool_json = {}
        pool_json['ticker'] = ticker.upper()
        pool_json['epochs'] = []
        progress_count += 1
        first_epoch = get_first_pool_epoch(tickers_json[ticker]);
        print('updating ' + str(progress_count) + ' of ' + str(len(tickers_to_update)) + ' - ' + ticker + '(' + str(first_epoch) + ',' + str(latest_epoch) + ')')
        for epoch in range(first_epoch, latest_epoch + 1):
            print('updating ' + str(progress_count) + ' of ' + str(len(tickers_to_update)) + ' - ' + ticker + ' - epoch ' + str(epoch))
            refresh_epoch(pool_json, tickers_json[ticker], epoch)

        recalculate_pool(pool_json)

        with open(data_folder + '/' + ticker.upper() + '.json', 'w') as outfile:
            json.dump(pool_json, outfile, indent=4, use_decimal=True)


add_missing_pools()