from datetime import timedelta
import logging

from src.base import Base
from src.constants import DATA_TYPES

logger = logging.getLogger(__name__)


class Data(Base):
    """
    Class to mutate the Strava and Libre data and combine them
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager

    @property
    def name(self):
        return "Strava-Libre"

    def get_records_between_timestamp(self, start_time, end_time):
        """
        Get the strava libre data between the end/start times
        """
        logger.debug(f"get_records_between_timestamp({start_time}, {end_time})")
        return self._get_records(start_time, end_time)

    def _get_records(self, start_time, end_time):
        logger.debug(f"_get_records({start_time}, {end_time})")
        return self.db_manager.get_records_between_timestamp(
            DATA_TYPES.STRAVA_LIBRE, start_time, end_time
        )

    def _get_last_record(self):
        logger.debug(f"Getting last record from {DATA_TYPES.STRAVA_LIBRE}")
        return self.db_manager.get_last_record(DATA_TYPES.STRAVA_LIBRE)

    def _get_glucose_records_within_interval(self, start_time, end_time):
        logger.debug(
            f"Getting glucose records within interval {start_time} - {end_time} for {DATA_TYPES.STRAVA_LIBRE}"
        )
        return self.db_manager.get_records_between_timestamp(
            DATA_TYPES.LIBRE, start_time, end_time
        )

    def combine_data(self):
        """
        Retrieve the last record in the DB relating to this data
        Get all strava data after that date.
        (We do not get all missing strava data as there may not be any glucose data,
        so we dont want to needlessely check it again.)
        Retrieve all the glucose data within those time ranges

        # TODO: Need to omit overllaping exercises (run/walk that are less than 60 minutes apart)
        """
        logger.info("*" * 50 + "\n" + " " * 20 + "combine_data()" + " " * 20 + "*" * 50)
        new_records = []
        _, last_id, last_checked_strava_id = self._get_last_record()
        new_entry_id = last_id + 1
        unchecked_strava_records = self.db_manager.get_filtered_by_id_records(
            DATA_TYPES.STRAVA, last_checked_strava_id
        )
        # Iterate through the unchecked records in the libre db to find them either side of a window
        for unchecked_strava_record in unchecked_strava_records:
            (
                current_strava_id,
                _,
                activity_type,
                _,
                _,
                activity_start_time,
                activity_end_time,
                _,
                _,
                _,
                _,
            ) = unchecked_strava_record
            start_time = activity_start_time - timedelta(seconds=3600)
            end_time = activity_end_time + timedelta(seconds=3600)
            libre_records = self._get_glucose_records_within_interval(
                start_time, end_time
            )
            for libre_record in libre_records:
                current_libre_id, current_glucose, current_timestamp = libre_record
                # ' Would be negative if activity_start_time instead of start time
                # but we just presume for now offset is always 60mins. More robust to
                # do -negatives from the start time though.'
                timestamp_since_start = (current_timestamp - start_time).total_seconds()
                new_records.append(
                    (
                        new_entry_id,
                        current_strava_id,
                        current_libre_id,
                        current_glucose,
                        current_timestamp,
                        activity_start_time,
                        activity_end_time,
                        activity_type,
                        timestamp_since_start,
                    )
                )
                # Increment index
                new_entry_id += 1
        self._save_data(new_records)

    def _save_data(self, records_to_save):
        logger.info(f"Saving {len(records_to_save)} to {DATA_TYPES.STRAVA_LIBRE}")
        if records_to_save:
            self.db_manager.save_data(records_to_save, DATA_TYPES.STRAVA_LIBRE)
        logger.info(
            f"Successfully saved {len(records_to_save)} to {DATA_TYPES.STRAVA_LIBRE}"
        )
