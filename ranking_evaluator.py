import simplejson as json


def add_pool_to_ranking_array(ranking_array, ticker):
    current_pool = {'rank': len(ranking_array) + 1, 'ticker': ticker}
    ranking_array.append(current_pool)


def safe_eval(expression, pool):
    allowed_names = {'pool': pool}
    code = compile(expression, "<string>", "eval")
    for name in code.co_names:
        if name not in allowed_names:
            raise NameError(f"The use of '{name}' is not allowed")

    return eval(code, {"__builtins__": {}}, allowed_names)


def evaluate_ranking(map_of_pool_jsons, ranking_name, number_of_pools_to_return):
    rankings_file = 'static/rankings.json'
    rankings_json = json.load(open(rankings_file))

    ranked_pools = []

    for ranking in rankings_json:
        if ranking['name'] == ranking_name:
            selected_ranking = ranking
            print('')
            print('')
            print(ranking['name'])
            print(ranking['description'])
            pools = []
            iter_count = 0
            for ticker in map_of_pool_jsons.keys():
                pool_json = map_of_pool_jsons[ticker]
                pool = {}
                iter_count += 1
                try:
                    pool['ticker'] = ticker
                    pool['latest_epoch_live_stake'] = pool_json['epochs'][len(pool_json['epochs']) - 1][
                        'pool_stake']
                    pool['latest_epoch_total_stake'] = pool_json['epochs'][len(pool_json['epochs']) - 1][
                        'total_stake']
                    pool['lifetime_epochs'] = len(pool_json['epochs'])
                    pool['max_positive_diff'] = pool_json['max_positive_diff']
                    pool['max_negative_diff'] = pool_json['max_negative_diff']
                    pool['cumulative_diff'] = pool_json['cumulative_diff']
                    pool['cumulative_expected_blocks'] = pool_json['cumulative_expected_blocks']
                    pool['cumulative_actual_blocks'] = pool_json['cumulative_actual_blocks']
                    pool['max_actual_blocks'] = pool_json['max_actual_blocks']
                    pool['max_expected_blocks'] = pool_json['max_expected_blocks']
                    pool['current_lifetime_luck'] = pool_json['current_lifetime_luck']
                    pool['max_epoch_blocks'] = pool_json['max_epoch_blocks']
                    pool['max_cumulative_diff'] = pool_json['max_cumulative_diff']
                    pool['highest_lifetime_luck'] = pool_json['highest_lifetime_luck']
                    pool['lowest_lifetime_luck'] = pool_json['lowest_lifetime_luck']
                    if pool['latest_epoch_live_stake'] > 0:
                        pool['ranking_field'] = safe_eval(ranking['expression'], pool)
                        pools.append(pool)
                except Exception as e:
                    print(e)

            sorted_by_underappreciated_performance = sorted(pools, key=lambda d: d['ranking_field'], reverse=True)

            for pool in sorted_by_underappreciated_performance:
                if len(ranking['filters']) == 0:
                    add_pool_to_ranking_array(ranked_pools, pool['ticker'])
                else:
                    for current_filter in ranking['filters']:
                        if safe_eval(current_filter['expression'], pool):
                            add_pool_to_ranking_array(ranked_pools, pool['ticker'])

    return_pools = []
    for ranked_pool in ranked_pools:
        if ranked_pool['rank'] <= number_of_pools_to_return:
            return_pools.append(ranked_pool)
            print(str(ranked_pool['rank']) + ' - ' + ranked_pool['ticker'])

    selected_ranking['results'] = return_pools

    return selected_ranking

