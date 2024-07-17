import psycopg2
from psycopg2 import sql
import datetime
import logging
from constants import DATA_TYPES, TABLE_SCHEMA

logger = logging.getLogger(__name__)


class PostgresManager:
    def __init__(self, user, password, host, db):
        self.user = user
        self.password = password
        self.host = host
        self.db = db

    @property
    def conn_params(self):
        return {
            "host": self.host,
            "dbname": self.db,
            "user": self.user,
            "password": self.password,
        }

    def save_data(self, data, data_type):
        """
        Save the data to the associated table
        """
        logging.debug("save_data()")
        self._validate_data_type(data_type)

        logging.debug(f"Trying to save data into {TABLE_SCHEMA.NAME[data_type]}")
        conn = psycopg2.connect(**self.conn_params)
        with conn:
            with conn.cursor() as curs:
                query = sql.SQL(
                    """INSERT INTO {table} ({table_columns}) VALUES ({entries})"""
                ).format(
                    table=sql.Identifier(TABLE_SCHEMA.NAME[data_type]),
                    table_columns=sql.SQL(", ").join(
                        map(sql.Identifier, TABLE_SCHEMA.COLUMNS[data_type])
                    ),
                    entries=sql.SQL(", ").join(
                        sql.Placeholder() * len(TABLE_SCHEMA.COLUMNS[data_type])
                    ),
                )
                curs.executemany(
                    query,
                    data,
                )

        # leaving contexts doesn't close the connection
        conn.close()

    def _validate_data_type(self, data_type):
        if data_type not in (DATA_TYPES.LIBRE, DATA_TYPES.STRAVA):
            raise ValueError(f"Invalid data_type {data_type}")

    def _get_default_last_record(self, data_type):
        self._validate_data_type(data_type)
        if data_type == DATA_TYPES.LIBRE:
            return (datetime.datetime(1970, 7, 11, 19, 45, 55), 0)
        if data_type == DATA_TYPES.STRAVA:
            return [datetime.datetime(1970, 7, 11, 19, 45, 55)]

    def get_last_record(self, data_type):
        """Fetch the last record in the table"""
        logging.debug("get_last_record()")
        self._validate_data_type(data_type)
        logger.debug(f"Saving to {TABLE_SCHEMA.NAME[data_type]}")
        conn = psycopg2.connect(**self.conn_params)

        with conn:
            with conn.cursor() as curs:
                curs.execute(
                    sql.SQL(
                        "SELECT {table_columns} FROM {table} ORDER BY {order_by} DESC LIMIT 1"
                    ).format(
                        table_columns=sql.SQL(", ").join(
                            map(sql.Identifier, TABLE_SCHEMA.SEARCH_COLUMNS[data_type])
                        ),
                        order_by=sql.Identifier(TABLE_SCHEMA.ORDER_BY[data_type]),
                        table=sql.Identifier(TABLE_SCHEMA.NAME[data_type]),
                    )
                )
                res = curs.fetchone()

        # leaving contexts doesn't close the connection
        conn.close()

        return res or self._get_default_last_record(data_type)
