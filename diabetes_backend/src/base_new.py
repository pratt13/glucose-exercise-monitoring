import logging

logger = logging.getLogger(__name__)


class BaseNew:
    @property
    def name(self):
        raise NotImplementedError("Not implemented class name")

    @property
    def table(self):
        raise NotImplementedError("Not implemented db table")

    def get_records_between_timestamp(self, start_time, end_time):
        """
        Get the strava libre data between the end/start times
        """
        logger.debug(f"get_records_between_timestamp({start_time}, {end_time})")
        return self._get_records(start_time, end_time)

    def _get_records(self, start_time, end_time):
        logger.debug(f"_get_records({start_time}, {end_time}) for {self.name}")
        return self.db_manager.get_records_between_timestamp(
            self.table, start_time, end_time
        )

    def _get_last_record(self):
        logger.debug(f"Getting last record from {self.name}")
        return self.db_manager.get_last_record(self.table)

    def _save_data(self, records_to_save):
        logger.info(f"Saving {len(records_to_save)} to {self.name}")
        if records_to_save:
            self.db_manager.save_data(records_to_save, self.table)
        logger.info(f"Successfully saved {len(records_to_save)} to {self.name}")
