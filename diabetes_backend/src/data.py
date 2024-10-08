from datetime import timedelta
import logging

from src.base import Base
from src.database.tables import Glucose, GlucoseExercise, Strava

logger = logging.getLogger(__name__)


class DataManager(Base):
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
            f"Getting glucose records within interval {start_time} - {end_time} for Glucose"
        )
        return self.db_manager.get_records_between_timestamp(
            Glucose, start_time, end_time
        )

    def combine_data(self):
        """
        Retrieve the last record in the DB relating to this data
        Get all strava data after that date.
        (We do not get all missing strava data as there may not be any glucose data,
        so we dont want to needlessly check it again.)
        Retrieve all the glucose data within those time ranges

        # TODO: Need to omit overlapping exercises (run/walk that are less than 60 minutes apart)
        """
        logger.info("*" * 50 + "\n" + " " * 20 + "combine_data()" + " " * 20 + "*" * 50)
        new_records = []
        # Get last record in the database
        last_record = self._get_last_record()
        last_id = last_record.id
        last_checked_strava_id = last_record.strava_id
        new_entry_id = last_id + 1
        unchecked_strava_records = self.db_manager.get_filtered_by_id_records(
            Strava, last_checked_strava_id
        )
        # Iterate through the unchecked records in the libre db to find them either side of a window
        for unchecked_strava_record in unchecked_strava_records:
            logger.debug(f"Processing {unchecked_strava_record}")
            libre_records = self._get_glucose_records_within_interval(
                unchecked_strava_record.start_time - timedelta(seconds=3600),
                unchecked_strava_record.end_time + timedelta(seconds=3600),
            )
            for libre_record in libre_records:
                # ' Would be negative if activity_start_time instead of start time
                # but we just presume for now offset is always 60mins. More robust to
                # do -negatives from the start time though.'
                timestamp_since_start = (
                    libre_record.timestamp - unchecked_strava_record.start_time
                ).total_seconds()
                new_records.append(
                    GlucoseExercise(
                        id=new_entry_id,
                        strava_id=unchecked_strava_record.id,
                        glucose_rec=libre_record,
                        glucose_id=libre_record.id,
                        distance=unchecked_strava_record.distance,
                        timestamp=libre_record.timestamp,
                        activity_start=unchecked_strava_record.start_time,
                        activity_end=unchecked_strava_record.end_time,
                        activity_type=unchecked_strava_record.activity_type,
                        seconds_since_start=timestamp_since_start,
                    )
                )
                # Increment index
                new_entry_id += 1
        self._save_data(new_records)
