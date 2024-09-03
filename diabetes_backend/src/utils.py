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


def aggregate_summary_glucose_data(data, date_index, glucose_index):
    """
    Compute overview summary data of the glucose
    """
    timestamps = list(
        map(lambda x: convert_time_to_str(x[date_index], STRAVA_DATETIME), data)
    )
    glucose_list = list(map(lambda x: float(x[glucose_index]), data))

    df = pd.DataFrame({"time": timestamps, "raw": glucose_list})
    # TODO: COmpute percenta

    df = df.groupby([pd.Grouper(key="time", freq="1D")])["raw"].agg(
        ["mean", "median", "var", "count", "std", "max", "min"]
    )
    # Crude hack for NaN
    df = df.fillna(0)
    return {
        "days": list(df.index.values),
        "number_of_lows": [],
        "number_of_highs": [],
        "percentage_in_target": [],
        "mean": df["mean"].to_list(),
        "std": df["std"].to_list(),
        "var": df["var"].to_list(),
        "median": df["median"].to_list(),
        "max": df["max"].to_list(),
        "min": df["min"].to_list(),
    }


def aggregate_strava_data(data, distance_index, activity_index):
    """
    Count the different types of activities by time interval returning the
    count and total distance covered
    """
    activity_list = list(map(lambda x: x[activity_index], data))
    distance_list = list(map(lambda x: x[distance_index], data))

    df = pd.DataFrame({"activity": activity_list, "distance": distance_list})
    df = df.groupby(["activity"])["distance"].agg(["sum", "count"])

    # Crude hack for NaN
    df = df.fillna(0)
    return {
        "activity": list(df.index.values),
        "total_distance": df["sum"].to_list(),
        "number_activities": df["count"].to_list(),
    }


def aggregate_strava_libre_glucose_data(
    data, time_index, glucose_index, interval_min=10
):
    """
    Bucket the data into intervals, default 10minute
    """
    timestamps = list(map(lambda x: x[time_index], data))
    glucose_list = list(map(lambda x: float(x[glucose_index]), data))

    df = pd.DataFrame({"time": timestamps, "raw": glucose_list})
    t_intervals = [
        t
        for t in range(
            min(timestamps), max(timestamps) + interval_min * 60, interval_min * 60
        )
    ]
    df = df.groupby(pd.cut(df["time"], t_intervals))["raw"].agg(
        ["mean", "median", "var", "count", "std", "max", "min"]
    )
    # Crude hack for NaN
    df = df.fillna(0)
    return {
        "intervals": t_intervals,
        "mean": df["mean"].to_list(),
        "count": df["count"].to_list(),
        "median": df["median"].to_list(),
        "var": df["var"].to_list(),
        "std": df["std"].to_list(),
        "max": df["max"].to_list(),
        "min": df["min"].to_list(),
    }


def run_sum_strava_data(data, timestamp_index, distance_index, activity_index):
    """
    Compute the running distance for the different activities across a time window

    Example
             timestamp             activity  distance  Grouped Cumulative Sum  number_activities
        0  2000-01-01 12:00:00     WALK       2.0                     2.0                  1
        1   2000-01-01 5:00:00      RUN      22.1                    22.1                  1
        2   2000-02-01 5:00:00     WALK       5.1                     7.1                  2
        3   2000-04-01 5:00:00      RUN       4.1                    26.2                  2
        4   2000-06-01 5:00:00      RUN       1.1                    27.3                  3
        5   2000-07-01 5:00:00     SWIM       5.0                     5.0                  1

    """
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    timestamp_list = list(map(lambda x: x[timestamp_index], ordered_data))
    activity_list = list(map(lambda x: x[activity_index], ordered_data))
    distance_list = list(map(lambda x: float(x[distance_index]), ordered_data))

    df = pd.DataFrame(
        {
            "timestamp": timestamp_list,
            "activity": activity_list,
            "distance": distance_list,
        }
    )
    # Crude hack for NaN
    df = df.fillna(0)
    df["total_distance"] = df[["activity", "distance"]].groupby(["activity"]).cumsum()
    df["number_activities"] = (
        df[["activity", "distance"]].groupby(["activity"]).cumcount() + 1
    )

    meta_df = df.groupby("activity").max()
    return {
        "timestamped_data": list(
            zip(
                df["timestamp"].to_list(),
                df["activity"].to_list(),
                df["total_distance"].to_list(),
                df["number_activities"].to_list(),
            )
        ),
        "meta_data": meta_df.to_dict(orient="index"),
    }
