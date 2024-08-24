import os
from datetime import datetime
from src.constants import DATABASE_DATETIME
import numpy as np


def compute_epoch(ts, fmt):
    # utc_time = datetime.strptime(ts, fmt)
    return (ts - datetime(1970, 1, 1)).total_seconds()


def convert_str_to_ts(ts, fmt):
    return datetime.strptime(ts, fmt)


def convert_ts_to_str(ts, fmt):
    return ts.strftime(fmt)


def load_libre_credentials_from_env():
    return (os.getenv("LIBRE_EMAIL"), os.getenv("LIBRE_PASSWORD"))


def load_strava_credentials_from_env():
    return (
        os.getenv("STRAVA_CLIENT_ID"),
        os.getenv("STRAVA_CLIENT_SECRET"),
        os.getenv("STRAVA_REFRESH_TOKEN"),
    )


def compute_time_series_average(data):
    """
    Given a list of tuples (time, value) compute the average glucose between
    the maximum windows.

    Method:
        - For each point take the value between the two and the time and sum them.
    """
    total = 0
    for idx in range(len(data) - 1):
        total += abs(float(data[idx][1] - data[idx + 1][1])) / abs(
            compute_time_diff(data[idx][2], data[idx + 1][2])
        )
    return total * abs(compute_time_diff(data[0][2], data[-1][2]))


def compute_time_diff(time1, time2):
    return (time1 - time2).total_seconds()


def window(size):
    return np.ones(size) / float(size)


def time_series_average(data, idx):
    target_tuple_list = list(map(lambda x: float(x[idx]), data))
    return np.convolve(target_tuple_list, window(100), "same").tolist()
