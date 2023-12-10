import traceback

import logging
import simplejson as json
import urllib.request

SPA_JSON_URL = 'https://raw.githubusercontent.com/SinglePoolAlliance/Registration/master/registry.json'


def safe_eval(expression, pool, spa_tickers):
    allowed_names = {'pool': pool, 'spa_tickers': spa_tickers}
    code = compile(expression, "<string>", "eval")
    for name in code.co_names:
        if name not in allowed_names:
            raise NameError(f"The use of '{name}' is not allowed")

    return eval(code, {"__builtins__": {}}, allowed_names)


def get_spa_tickers():
    ret = []
    spa_json = json.load(urllib.request.urlopen(SPA_JSON_URL))
    for pool in spa_json:
        ret.append(pool['ticker'])
    return ret;


def set_dict_value_with_highest_lowest(dict, absolute, key, value):
    dict[key] = value
    if key + '__highest' not in absolute:
        absolute[key + '__highest'] = float('-inf')
    if key + '__lowest' not in absolute:
        absolute[key + '__lowest'] = float('inf')
    if value > absolute[key + '__highest']:
        absolute[key + '__highest'] = value
    if value < absolute[key + '__lowest']:
        absolute[key + '__lowest'] = value


def set_normalized_value(dict, absolute, key):
    dict[key + '__normalized'] = dict[key] / (absolute[key + '__highest'] - absolute[key + '__lowest'])


def evaluate_ranking(map_of_pool_jsons, ranking_name, number_of_pools_to_return):
    spa_tickers = get_spa_tickers()
    rankings_file = 'static/rankings.json'
    rankings_json = json.load(open(rankings_file))

    filtered_pools = []

    for ranking in rankings_json:
        if ranking['name'] == ranking_name:
            selected_ranking = ranking
            print('')
            print('')
            print(ranking['name'])
            print(ranking['description'])
            pools = []
            absolute = {}
            iter_count = 0

            # first pass, set all values with highest and lowest
            for ticker in map_of_pool_jsons.keys():
                logging.info(f'first pass ' + ticker)
                pool_json = map_of_pool_jsons[ticker]
                pool = {}
                iter_count += 1
                try:
                    pool['ticker'] = ticker
                    pool['id'] = map_of_pool_jsons[ticker]['id']
                    if len(pool_json['epochs']) > 0:
                        set_dict_value_with_highest_lowest(pool, absolute, 'latest_epoch_pool_stake', pool_json['epochs'][len(pool_json['epochs']) - 1]['pool_stake'])
                    else:
                        set_dict_value_with_highest_lowest(pool, absolute, 'latest_epoch_pool_stake', 0)
                    set_dict_value_with_highest_lowest(pool, absolute, 'lifetime_epochs', len(pool_json['epochs']))
                    set_dict_value_with_highest_lowest(pool, absolute, 'max_positive_diff', pool_json['max_positive_diff'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'max_negative_diff', pool_json['max_negative_diff'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'cumulative_diff', pool_json['cumulative_diff'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'cumulative_expected_blocks', pool_json['cumulative_expected_blocks'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'cumulative_actual_blocks', pool_json['cumulative_actual_blocks'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'max_actual_blocks', pool_json['max_actual_blocks'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'max_expected_blocks', pool_json['max_expected_blocks'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'current_lifetime_luck', pool_json['current_lifetime_luck'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'max_epoch_blocks', pool_json['max_epoch_blocks'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'max_cumulative_diff', pool_json['max_cumulative_diff'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'highest_lifetime_luck', pool_json['highest_lifetime_luck'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'lowest_lifetime_luck', pool_json['lowest_lifetime_luck'])
                    set_dict_value_with_highest_lowest(pool, absolute, 'blocks_in_last_ten_epochs', pool_json['blocks_in_last_ten_epochs'])
                    pools.append(pool)
                except Exception as e:
                    print(e)
                    print(pool['ticker'])
                    traceback.print_exc()

            # second pass, set normalized values
            for pool in pools:
                logging.info(f'second pass ' + pool['ticker'])
                set_normalized_value(pool, absolute, 'latest_epoch_pool_stake')
                set_normalized_value(pool, absolute, 'lifetime_epochs')
                set_normalized_value(pool, absolute, 'max_positive_diff')
                set_normalized_value(pool, absolute, 'max_negative_diff')
                set_normalized_value(pool, absolute, 'cumulative_diff')
                set_normalized_value(pool, absolute, 'cumulative_expected_blocks')
                set_normalized_value(pool, absolute, 'cumulative_actual_blocks')
                set_normalized_value(pool, absolute, 'max_actual_blocks')
                set_normalized_value(pool, absolute, 'max_expected_blocks')
                set_normalized_value(pool, absolute, 'current_lifetime_luck')
                set_normalized_value(pool, absolute, 'max_epoch_blocks')
                set_normalized_value(pool, absolute, 'max_cumulative_diff')
                set_normalized_value(pool, absolute, 'highest_lifetime_luck')
                set_normalized_value(pool, absolute, 'lowest_lifetime_luck')
                set_normalized_value(pool, absolute, 'blocks_in_last_ten_epochs')

            for pool in pools:
                logging.info(f'evaluating pool ' + pool['ticker'])
                if len(ranking['filters']) == 0:
                    filtered_pools.append(pool)
                else:
                    passes_all_filters = True
                    for current_filter in ranking['filters']:
                        if not safe_eval(current_filter['expression'], pool, spa_tickers):
                            logging.info(f'pool ' + pool['ticker'] + ' failed filter ' + current_filter['expression'])
                            passes_all_filters = False
                            break
                    if passes_all_filters:
                        filtered_pools.append(pool)

            logging.info(f'pools left after filtering ' + str(len(filtered_pools)))

            for pool in filtered_pools:
                pool['ranking_field'] = safe_eval(ranking['expression'], pool, spa_tickers)

    sorted_by_ranking_field = sorted(filtered_pools, key=lambda d: d['ranking_field'], reverse=True)

    return_pools = []

    if number_of_pools_to_return > len(sorted_by_ranking_field):
        number_of_pools_to_return = len(sorted_by_ranking_field)
    for rank in range(0, number_of_pools_to_return):
        logging.info(f'returning ticker ' + str(sorted_by_ranking_field[rank]['ticker']) + ' id ' + sorted_by_ranking_field[rank]['id'])
        sorted_by_ranking_field[rank]['rank'] = rank
        return_pools.append(sorted_by_ranking_field[rank])

    selected_ranking['results'] = return_pools

    return selected_ranking

