import os
import logging
import threading
from queue import Queue
from abc import abstractmethod, ABC
from update_library import is_in_quiet_period, add_all_missing_epochs, reorder_pool, refresh_epoch, recalculate_pool, get_latest_epoch, data_folder
import simplejson as json
from datetime import datetime
from config import config
import psycopg2
from psycopg2.extras import RealDictCursor
from time import sleep
from thread_safe_objects import ThreadSafeDictOfPoolJson


TASKS_QUEUE = Queue()


class BackgroundThread(threading.Thread, ABC):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def _stopped(self) -> bool:
        return self._stop_event.is_set()

    @abstractmethod
    def startup(self) -> None:
        """
        Method that is called before the thread starts.
        Initialize all necessary resources here.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def shutdown(self) -> None:
        """
        Method that is called shortly after stop() method was called.
        Use it to clean up all resources before thread stops.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def handle(self) -> None:
        """
        Method that should contain business logic of the thread.
        Will be executed in the loop until stop() method is called.
        Must not block for a long time.
        :return: None
        """
        raise NotImplementedError()

    def run(self) -> None:
        """
        This method will be executed in a separate thread
        when start() method is called.
        :return: None
        """
        self.startup()
        while not self._stopped():
            self.handle()
        self.shutdown()


class UpdateThread(BackgroundThread):
    def __init__(self, map_of_pool_jsons):
        self.map_of_pool_jsons = map_of_pool_jsons
        super().__init__()

    def startup(self) -> None:
        logging.info('UpdateThread started')

    def shutdown(self) -> None:
        logging.info('UpdateThread stopped')

    def handle(self) -> None:
        print('adding any missing epochs for all pools')
        add_all_missing_epochs(self.map_of_pool_jsons)
        print('done adding any missing epochs for all pools')
        if not is_in_quiet_period():
            latest_epoch = get_latest_epoch()
            updates_file_name = 'static/updates.json'
            pool_tickers_file_name = 'static/pool_tickers.json'

            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            print("Current Time =", current_time)

            updates_json = json.load(open(updates_file_name))
            pool_tickers_json = json.load(open(pool_tickers_file_name))

            last_update_time = updates_json[len(updates_json)-1]['time']

            current_update = {'time': current_time, 'last_time': last_update_time}

            conn = None
            try:
                print("fetching pools with blocks since " + last_update_time)
                params = config()
                conn = psycopg2.connect(**params)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                query = """ SELECT DISTINCT pool_hash.view
                            FROM block 
                            INNER JOIN slot_leader ON slot_leader.id = block.slot_leader_id
                            INNER JOIN pool_hash ON pool_hash.id = slot_leader.pool_hash_id
                            WHERE TIME > \'""" + last_update_time + "\' ;"""
                cursor.execute(query)
                query_results = cursor.fetchall()
                cursor.close()

                valid_pools_needing_updates = []
                for row in query_results:
                    if row['view'] in pool_tickers_json:
                        current_pool_needing_update = {}
                        current_pool_needing_update['view'] = row['view']
                        current_pool_needing_update['ticker'] = pool_tickers_json[row['view']]
                        valid_pools_needing_updates.append(current_pool_needing_update)

                if len(valid_pools_needing_updates) > 0:
                    current_update['updates'] = len(valid_pools_needing_updates)
                    updates_json.append(current_update)
                    with open(updates_file_name, 'w') as outfile:
                        json.dump(updates_json, outfile, indent=4, use_decimal=True)
                else:
                    print('nothing to update - waiting a few seconds')

                print('out of ' + str(len(query_results)) + ' keeping ' + str(len(valid_pools_needing_updates)) + ' that have working tickers')

                processing_count = 0
                for row in valid_pools_needing_updates:
                    processing_count += 1
                    print('processing ' + str(processing_count) + ' of ' + str(len(valid_pools_needing_updates)) + ' - ' + row['ticker'].upper())
                    try:
                        pool_json_path = data_folder + "/" + row['ticker'].upper() + ".json"
                        pool_json = json.load(open(pool_json_path))
                        refresh_epoch(pool_json, row['view'], latest_epoch - 1)
                        refresh_epoch(pool_json, row['view'], latest_epoch)

                        recalculate_pool(pool_json)
                        reorder_pool(pool_json)

                        with open(data_folder + '/' + row['ticker'].upper() + '.json', 'w') as outfile:
                            json.dump(pool_json, outfile, indent=4, use_decimal=True)

                    except (Exception) as metadata_error:
                        print(metadata_error)

            except (Exception, psycopg2.DatabaseError) as error:
                print("Error: " + str(error))
            finally:
                if conn is not None:
                    conn.close()
            sleep(1)

class BackgroundThreadFactory:
    @staticmethod
    def create(thread_type: str) -> BackgroundThread:
        if thread_type == 'update':
            return UpdateThread()

        raise NotImplementedError('Specified thread type is not implemented.')
