import simplejson as json

def is_ticker_in_spa(ticker):
    with open("static/spa.json", encoding='utf-8') as data_file:
        spa_json = json.load(data_file)
        for spa_pool in spa_json:
            if spa_pool['ticker'] == ticker:
                return True
    return False

def getTwitterHandleForTicker(ticker):
    with open("static/spa.json", encoding='utf-8') as data_file:
        spa_json = json.load(data_file)
        for spa_pool in spa_json:
            if spa_pool['ticker'] == ticker:
                return spa_pool['social']['twitter']
    return ''

pools = []
tickers_json = json.load(open('static/tickers.json'))
for (pool_ticker, pool_id) in tickers_json.items():
    pool = {}
    pool['cumulative_diff'] = 0
    pool['cumulative_epochs'] = 0
    pool['cumulative_blocks'] = 0
    pool['live_stake'] = 0
    pool['ticker'] = pool_ticker
    pool_file = "data/" + pool_ticker.upper() + ".json"
    if True:
        try:
            pool_json = json.load(open(pool_file))
            for epoch in pool_json['epochs']:
                epoch_diff = epoch['actual'] - epoch['expected']
                pool['cumulative_diff'] += epoch_diff
                pool['cumulative_epochs'] += 1
                pool['cumulative_blocks'] += epoch['actual']
                pool['live_stake'] = epoch['pool_stake']
                pool['total_stake'] = epoch['total_stake']
            pool['block_performance'] = pool['cumulative_diff'] * pool['cumulative_blocks']
            pool['epochs_performance'] = pool['cumulative_diff'] * pool['cumulative_epochs']
            pool['total_performance'] = pool['cumulative_diff'] * pool['cumulative_blocks'] * pool['cumulative_epochs']
            pool['underapreciated'] = pool['cumulative_diff'] * pool['cumulative_epochs'] / (pool['live_stake'] / pool['total_stake'])
            pools.append(pool)
        except (Exception) as error:
            print("Unable to load " + pool_ticker)
            print(repr(error))

performers = []
print("underapreciated")
sorted_by_underapreciated_performance = sorted(pools, key=lambda d: d['underapreciated'], reverse=True)
rank = 0
for pool in sorted_by_underapreciated_performance:
    if rank < 70:
        if (pool['live_stake'] > 100000000000):
            if is_ticker_in_spa(pool['ticker']):
                current_performer = {}
                rank += 1
                current_performer['rank'] = rank
                current_performer['ticker'] = pool['ticker']
                current_performer['twitter'] = getTwitterHandleForTicker(pool['ticker'])
                performers.append(current_performer)
                print(str(rank) + " " + pool['ticker'] + " - " + current_performer['twitter'] + " - " + str(pool['live_stake']/1000000) + " - " + str(pool['underapreciated']))
with open('static/performers.json', 'w') as outfile:
    json.dump(performers, outfile, indent=4, use_decimal=True)


