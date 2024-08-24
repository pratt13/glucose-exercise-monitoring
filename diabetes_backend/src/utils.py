import os
from datetime import datetime


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
        total += abs(data[idx][1] - data[idx + 1][1]) / abs(
            compute_time_diff(data[idx][2], data[idx + 1][2])
        )
    return total


def compute_time_diff(time1, time2):
    return (convert_str_to_ts(time1) - convert_str_to_ts(time2)).total_seconds()
