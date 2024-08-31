import logging

from src.constants import DATA_TYPES


logger = logging.getLogger(__name__)


class Data:
    """
    Class to mutate the Strava and Libre data and combine them
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def combine_data(self):
        """
        Retrieve the last record in the DB relating to this data
        Get all strava data after that date
        Retrieve all the glucose data within those time ranges
        """
        logger.debug("***********************************************")
        logger.debug("combine_data()")
        new_records = []
        last_strava_libre_record = self.db_manager.get_last_record(
            DATA_TYPES.STRAVA_LIBRE
        )
        logger.debug(f"last_strava_libre_record: {last_strava_libre_record}")
        checked_strava_id = last_strava_libre_record[2]
        unchecked_strava_records = self.db_manager.get_filtered_by_id_records(
            DATA_TYPES.STRAVA, checked_strava_id
        )
        logger.debug(f"unchecked_strava_records: {unchecked_strava_records}")
        new_entry_id = last_strava_libre_record[1]
        # Iterate through the unchecked records in the libre db to find them either side of a window
        for unchecked_strava_record in unchecked_strava_records:
            start_time = unchecked_strava_record[5]
            end_time = unchecked_strava_record[6]
            libre_records = self.db_manager.get_last_record(
                DATA_TYPES.LIBRE, start_time, end_time
            )
            for libre_record in libre_records:
                new_records.append(
                    (new_entry_id, last_strava_libre_record, libre_record)
                )
                # Increment index
                new_entry_id += 1
        logger.debug(f"new_records: {new_records}")
        self.db_manager.save_data(new_records, DATA_TYPES.STRAVA_LIBRE)
