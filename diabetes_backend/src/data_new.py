from datetime import timedelta
import logging

from src.base_new import BaseNew
from src.database.tables import GlucoseExercise, Strava

logger = logging.getLogger(__name__)


class Data(BaseNew):
    """
    Class to mutate the Strava and Libre data and combine them
    """

    @property
    def name(self):
        return "GlucoseExercise"

    @property
    def table(self):
        return GlucoseExercise

    def _get_glucose_records_within_interval(self, start_time, end_time):
        logger.debug(
            f"Getting glucose records within interval {start_time} - {end_time} for {self.name}"
        )
        return self.db_manager.get_records_between_timestamp(
            self.table, start_time, end_time
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
            Strava, last_checked_strava_id
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
            start_time = unchecked_strava_record.start_time - timedelta(seconds=3600)
            end_time = unchecked_strava_record.end_time + timedelta(seconds=3600)
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
