import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.database.glucose import Glucose

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine

    def save_data(self, data):
        """
        Save the data to the associated table
        """
        logging.debug("save_data()")
        with Session(self.engine) as session:
            session.add_all(data)
            session.commit()

    def _validate_data_type(self, table):
        if isinstance(table, Glucose):
            raise ValueError(f"Invalid data_type {table}")

    def _get_default_last_record(self, table):
        self._validate_data_type(table)
        if type(table) is type(Glucose):
            logger.debug("Returning glucose record")
            rec = Glucose(
                id=1, timestamp=datetime.datetime(1970, 7, 11, 19, 45, 55), glucose=5.0
            )
            logger.debug(rec)
            return rec
        raise ValueError(
            f"Cannot get default last record as {table} is not a valid table"
        )

    def get_last_record(self, table):
        """Fetch the last record in the table"""
        logger.info(f"Getting last record of {table}")
        self._validate_data_type(table)
        logger.debug("+++++++++++++++++++++++++++++++++")
        stmt = select(table).order_by(table.id.desc()).limit(1)
        logger.debug("start")
        with Session(self.engine) as session:
            rec = session.execute(stmt).first()
            # TODO: There is only one record possible as limit 1
            logger.debug(rec)
            res = rec or self._get_default_last_record(table)
        logger.debug("+++++++++++++++++++++++++++++++++")
        return res

    def get_records_between_timestamp(self, table, start_time, end_time):
        """Fetch the records in the table for the given date range"""
        logging.debug(f"get_last_record({table})")
        self._validate_data_type(table)
        logger.debug(f"Retrieving data from {table}")
        stmt = select(table).where(
            table.timestamp <= end_time and start_time <= table.timestamp
        )
        with Session(self.engine) as session:
            logger.debug("================")
            recs = session.execute(stmt)
            res = [rec for rec in recs]
        return res or []

    def get_filtered_by_id_records(self, table, id):
        """Fetch the records greater than the given id"""
        logging.debug(f"get_filtered_by_id_records({table})")
        self._validate_data_type(table)
        logger.debug(f"Retrieving data from {table}")
        stmt = select(table).where(table.id > id).order_by(table.id.asc())
        with Session(self.engine) as session:
            recs = session.execute(stmt)
            res = [rec for rec in recs]
        return res or []
