import os
import simplejson as json
from ranking_evaluator import evaluate_ranking
from thread_safe_objects import ThreadSafeDictOfPoolJson


map_of_pool_jsons = ThreadSafeDictOfPoolJson()
directory = 'data/'
all_files = os.listdir(directory)
for filename in all_files:
    pool_file = os.path.join(directory, filename)
    if os.path.isfile(pool_file):
        pool_json = json.load(open(pool_file))
        map_of_pool_jsons[pool_json['ticker']] = pool_json

ranking = evaluate_ranking(map_of_pool_jsons, 'underappreciated_performers', 100)
for pool in ranking['results']:
    print(str(pool['rank']) + ' - ' + pool['ticker'] + ' - ' + str(pool['current_lifetime_luck__normalized']) + ' - ' + str(pool['cumulative_diff__normalized']) + ' - ' + str(pool['lifetime_epochs__normalized']) + ' - ' + str(pool['latest_epoch_pool_stake__normalized']) + ' - ' + str((pool['current_lifetime_luck__normalized'] * pool['lifetime_epochs__normalized']) - pool['latest_epoch_pool_stake__normalized']))
