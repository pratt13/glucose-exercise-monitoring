import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, literal_column
from src.database.tables import Glucose, Strava, GlucoseExercise

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine

    @property
    def name(self):
        return "DatabaseManager"

    def save_data(self, data):
        """
        Save the data to the associated table
        """
        logging.debug("save_data()")
        with Session(self.engine) as session:
            session.add_all(data)
            session.commit()

    def _validate_data_type(self, table):
        if table not in (Glucose, Strava, GlucoseExercise):
            raise ValueError(f"Invalid data_type {table}")

    def _get_default_last_record(self, table):
        self._validate_data_type(table)
        if table == Glucose:
            rec = Glucose(
                id=0,
                timestamp=datetime.datetime(1970, 7, 11, 19, 45, 55).astimezone(
                    datetime.timezone.utc
                ),
                glucose=5.0,
            )
            logger.debug(f"Returning default glucose record: {rec}")
            return rec
        elif table == Strava:
            rec = Strava(id=0, start_time=datetime.datetime(1970, 7, 11, 19, 45, 55))
            logger.debug(f"Returning default strava record: {rec}")
            return rec
        elif table == GlucoseExercise:
            # No record strava and glucose id are 0
            rec = GlucoseExercise(
                id=0,
                timestamp=datetime.datetime(1970, 7, 11, 19, 45, 55).astimezone(
                    datetime.timezone.utc
                ),
                strava_id=0,
                glucose_id=0,
            )
            logger.debug(f"Returning default GlucoseExercise record: {rec}")
            return rec

        raise ValueError(
            f"Cannot get default last record as {table} is not a valid table"
        )

    def get_last_record(self, table):
        """Fetch the last record in the table"""
        logger.info(f"Getting last record of {table}")
        self._validate_data_type(table)
        stmt = select(table).order_by(table.id.desc()).limit(1)
        with Session(self.engine) as session:
            rec = session.execute(stmt).scalar()
            res = rec or self._get_default_last_record(table)
        return res

    def get_records_between_timestamp(self, table, start, end, time_column="timestamp"):
        """Fetch the records in the table for the given date range"""
        logging.debug(f"get_records_between_timestamp({start},{end},{time_column})")
        self._validate_data_type(table)
        stmt = select(table).where(
            (literal_column(time_column) <= end)
            & (start <= literal_column(time_column))
        )
        with Session(self.engine) as session:
            recs = session.execute(stmt)
            res = [rec[0] for rec in recs]
        return res or []

    def get_filtered_by_id_records(self, table, id):
        """Fetch the records greater than the given id"""
        logging.debug(f"get_filtered_by_id_records({table}, {id})")
        self._validate_data_type(table)
        logger.debug(f"Retrieving data from {table}")
        stmt = select(table).where(table.id > id).order_by(table.id.asc())
        with Session(self.engine) as session:
            recs = session.execute(stmt)
            res = [rec[0] for rec in recs]
        return res or []
