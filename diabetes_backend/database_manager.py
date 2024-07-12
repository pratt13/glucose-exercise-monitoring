import psycopg2
from psycopg2 import sql
import datetime
from constants import DATABASE_TABLE, DATETIME_FORMAT


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

    def save_glucose_data(self, data):
        """
        Save the data to the table
        """
        conn = psycopg2.connect(**self.conn_params)

        with conn:
            with conn.cursor() as curs:
                curs.executemany(
                    "INSERT INTO glucose_times (id, glucose, timestamp) VALUES (%s, %s, %s)", data
                )
        # leaving contexts doesn't close the connection
        conn.close()

    def get_last_record(self):
        """Fetch the last record in the table"""
        conn = psycopg2.connect(**self.conn_params)

        with conn:
            with conn.cursor() as curs:
                curs.execute(
                    sql.SQL(
                        "SELECT timestamp, id FROM {table} ORDER BY timestamp DESC LIMIT 1"
                    ).format(
                        table=sql.Identifier(DATABASE_TABLE),
                    )
                )
                res = curs.fetchone()

        # leaving contexts doesn't close the connection
        conn.close()

        return res or (datetime.datetime(1990, 7, 11, 19, 45, 55), 0)
