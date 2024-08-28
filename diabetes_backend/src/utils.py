import os
from datetime import datetime
from src.constants import STRAVA_DATETIME, TIME_FMT
import numpy as np
import pandas as pd

import logging

logger = logging.getLogger(__name__)


def compute_epoch(ts):
    return int(ts.strftime("%s"))


def convert_str_to_ts(ts, fmt):
    return datetime.strptime(ts, fmt)


def convert_ts_to_str(ts, fmt):
    return ts.strftime(fmt)


def convert_time_to_str(ts, fmt):
    return ts.strftime(fmt)


def load_libre_credentials_from_env():
    return (os.getenv("LIBRE_EMAIL"), os.getenv("LIBRE_PASSWORD"))


def load_strava_credentials_from_env():
    return (
        os.getenv("STRAVA_CLIENT_ID"),
        os.getenv("STRAVA_CLIENT_SECRET"),
        os.getenv("STRAVA_REFRESH_TOKEN"),
        os.getenv("STRAVA_CODE"),
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


def aggregate_glucose_data(data, date_index, glucose_index, interval="15min"):
    """
    Bucket the data into intervals, default 15minute
    Compute the average
    Variance
    """
    timestamps = list(
        map(lambda x: convert_time_to_str(x[date_index], STRAVA_DATETIME), data)
    )
    glucose_list = list(map(lambda x: float(x[glucose_index]), data))

    df = pd.DataFrame({"time": timestamps, "raw": glucose_list})
    # COnvert to dt and replace all the yyy/mm/dd with the same as we only want hours
    # may want to do pd series instead at some point
    df["time"] = pd.to_datetime(df["time"]).apply(
        lambda t: t.replace(day=31, year=2000, month=12)
    )
    raw_data = (
        df.groupby([pd.Grouper(key="time", freq=interval)])["raw"].apply(list).to_list()
    )

    df = df.groupby([pd.Grouper(key="time", freq=interval)])["raw"].agg(
        ["mean", "median", "var", "count", "std", "max", "min"]
    )
    # Format the time column
    df.index = df.index.strftime("%H:%M")
    # Crude hack for NaN
    df = df.fillna(0)
    return {
        "intervals": list(df.index.values),
        "mean": df["mean"].to_list(),
        "count": df["count"].to_list(),
        "median": df["median"].to_list(),
        "var": df["var"].to_list(),
        "raw": raw_data,
        "std": df["std"].to_list(),
        "max": df["max"].to_list(),
        "min": df["min"].to_list(),
    }
