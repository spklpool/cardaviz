import simplejson as json
import os

tickers_json = json.load(open('static/tickers.json'))

directory = 'data'
for filename in os.listdir(directory):
    pool_file = os.path.join(directory, filename)
    if os.path.isfile(pool_file):
        pool_json = json.load(open(pool_file))
        pool_ticker = pool_json['ticker']
        has_blocks = False
        last_pool_stake = 0
        for epoch in pool_json['epochs']:
            last_pool_stake = epoch['pool_stake']
            if epoch['actual'] > 0:
                has_blocks = True
                break
        if has_blocks == False:
            print(pool_ticker + " - " + str(last_pool_stake / 1000000))


