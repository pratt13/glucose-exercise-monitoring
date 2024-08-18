import sys, os, unittest
from unittest import mock
from datetime import datetime as dt
from psycopg2 import sql

# Mangle the paths in tests not in the code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database_manager import PostgresManager
from src.constants import DATA_TYPES, DATETIME_FORMAT, DATABASE_TABLE, TABLE_SCHEMA

EXAMPLE_DATA = [
    [dt.strptime("12/31/2000 10:30:00 AM", DATETIME_FORMAT), 1],
    [dt.strptime("12/31/2000 10:20:00 AM", DATETIME_FORMAT), 2],
    [dt.strptime("12/31/2000 10:10:00 AM", DATETIME_FORMAT), 3],
    [dt.strptime("12/31/2000 10:00:00 AM", DATETIME_FORMAT), 4],
    [dt.strptime("12/31/2000 09:30:00 AM", DATETIME_FORMAT), 5],
]


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.conn_values = {
            "user": "user",
            "password": "password",
            "host": "host",
            "dbname": "dbname",
        }
        self.PostgresManager = PostgresManager(*self.conn_values.values())

    @mock.patch("psycopg2.connect")
    def test_get_last_record(self, mock_connect):
        for call_count, (data_type, query_str) in enumerate(
            zip(
                [DATA_TYPES.LIBRE, DATA_TYPES.STRAVA],
                (
                    sql.SQL(
                        "SELECT {table_columns} FROM {table} ORDER BY {order_by} DESC LIMIT 1"
                    ).format(
                        table_columns=sql.SQL(", ").join(
                            map(
                                sql.Identifier,
                                TABLE_SCHEMA.SEARCH_COLUMNS[DATA_TYPES.LIBRE],
                            )
                        ),
                        order_by=sql.Identifier(
                            TABLE_SCHEMA.ORDER_BY[DATA_TYPES.LIBRE]
                        ),
                        table=sql.Identifier(TABLE_SCHEMA.NAME[DATA_TYPES.LIBRE]),
                    ),
                    sql.SQL(
                        "SELECT {table_columns} FROM {table} ORDER BY {order_by} DESC LIMIT 1"
                    ).format(
                        table_columns=sql.SQL(", ").join(
                            map(
                                sql.Identifier,
                                TABLE_SCHEMA.SEARCH_COLUMNS[DATA_TYPES.STRAVA],
                            )
                        ),
                        order_by=sql.Identifier(
                            TABLE_SCHEMA.ORDER_BY[DATA_TYPES.STRAVA]
                        ),
                        table=sql.Identifier(TABLE_SCHEMA.NAME[DATA_TYPES.STRAVA]),
                    ),
                ),
            ),
            start=1,
        ):
            with self.subTest(data_type=data_type, query_str=query_str):
                mock_con = (
                    mock_connect.return_value
                )  # result of psycopg2.connect(**connection_stuff)
                mock_cur = (
                    mock_con.cursor.return_value.__enter__.return_value
                )  # result of con.cursor()
                mock_cur.fetchone.return_value = EXAMPLE_DATA[
                    0
                ]  # return this when calling cur.fetchone()

                result = self.PostgresManager.get_last_record(data_type)

                self.assertEqual(result, EXAMPLE_DATA[0])

                # Check the calls are as expected
                mock_connect.assert_called_with(**self.conn_values)
                mock_con.cursor.asset_called_with(data_type)
                self.assertEqual(mock_cur.execute.call_count, call_count)
                mock_cur.execute.assert_called_with(query_str)

    @mock.patch("psycopg2.connect")
    def test_save_data(self, mock_connect):
        for call_count, (data_type, query_str, test_data) in enumerate(
            zip(
                [DATA_TYPES.LIBRE, DATA_TYPES.STRAVA],
                [
                    sql.SQL(
                        """INSERT INTO {table} ({table_columns}) VALUES ({entries})"""
                    ).format(
                        table=sql.Identifier(TABLE_SCHEMA.NAME[DATA_TYPES.LIBRE]),
                        table_columns=sql.SQL(", ").join(
                            map(sql.Identifier, TABLE_SCHEMA.COLUMNS[DATA_TYPES.LIBRE])
                        ),
                        entries=sql.SQL(", ").join(
                            sql.Placeholder()
                            * len(TABLE_SCHEMA.COLUMNS[DATA_TYPES.LIBRE])
                        ),
                    ),
                    sql.SQL(
                        """INSERT INTO {table} ({table_columns}) VALUES ({entries})"""
                    ).format(
                        table=sql.Identifier(TABLE_SCHEMA.NAME[DATA_TYPES.STRAVA]),
                        table_columns=sql.SQL(", ").join(
                            map(sql.Identifier, TABLE_SCHEMA.COLUMNS[DATA_TYPES.STRAVA])
                        ),
                        entries=sql.SQL(", ").join(
                            sql.Placeholder()
                            * len(TABLE_SCHEMA.COLUMNS[DATA_TYPES.STRAVA])
                        ),
                    ),
                ],
                [
                    [
                        (1, 4.5, dt(1990, 7, 11, 19, 45, 55)),
                        (2, 4.5, dt(1990, 7, 11, 19, 45, 55)),
                    ],
                    [
                        (1, 1.2, "RUN", 10, 145, "ts", "ts2", 1.2, 1.3, 1.4, 1.5),
                        (2, 1.2, "RUN2", 10, 145, "ts", "ts2", 1.2, 1.3, 1.4, 1.5),
                    ],
                ],
            ),
            start=1,
        ):
            with self.subTest(
                data_type=data_type, query_str=query_str, test_data=test_data
            ):

                mock_con = (
                    mock_connect.return_value
                )  # result of psycopg2.connect(**connection_stuff)
                mock_cur = (
                    mock_con.cursor.return_value.__enter__.return_value
                )  # result of con.cursor()

                self.PostgresManager.save_data(test_data, data_type)

                # Check the calls are as expected
                mock_connect.assert_called_with(**self.conn_values)
                mock_con.cursor.asset_called_with()
                self.assertEqual(mock_cur.executemany.call_count, call_count)
                mock_cur.executemany.assert_called_with(query_str, test_data)
