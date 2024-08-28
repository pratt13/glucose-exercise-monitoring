import os
from datetime import datetime
from src.constants import DATABASE_DATETIME, STRAVA_DATETIME, TIME_FMT
import numpy as np

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


def aggregate_average(time_list, glucose_list, window_size=100):
    return list(
        zip(time_list, np.convolve(glucose_list, window(window_size), "valid").tolist())
    )


def nday_average(data, date_index, glucose_index, days):
    time_list = sorted(
        list(map(lambda x: convert_time_to_str(x[date_index].time(), TIME_FMT), data))
    )
    glucose_list = list(map(lambda x: float(x[glucose_index]), data))
    if days == 7:
        return aggregate_average(time_list, glucose_list)
    else:
        raise NotImplementedError


def aggregate_data(data, date_index, glucose_index):
    time_list = list(
        map(lambda x: convert_time_to_str(x[date_index].time(), TIME_FMT), data)
    )
    glucose_list = list(map(lambda x: float(x[glucose_index]), data))
    combined_data = sorted(list(zip(time_list, glucose_list)), key=lambda x: x[0])
    return {
        "average": aggregate_average(*zip(*combined_data)),
        "average_window_10": aggregate_average(
            *zip(*combined_data), window_size=int(len(combined_data) / (24 * 5))
        ),
        "raw": combined_data,
    }


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
    import pandas as pd

    df = pd.DataFrame({"time": timestamps, "raw": glucose_list})
    # COnvert to dt and replace all the yyy/mm/dd with the same as we only want hours
    # may want to do pd series instead at some point
    df["time"] = pd.to_datetime(df["time"]).apply(
        lambda t: t.replace(day=31, year=2000, month=12)
    )
    raw_data = (
        df.groupby(pd.Grouper(key="time", freq=interval))["raw"].apply(list).to_list()
    )

    # ## Aggregate the data into 5 minute intervals
    # agg_df = df.groupby(pd.Grouper(key='time', freq='5min')).count()
    # agg_df["Mean"] = df.groupby(pd.Grouper(key='time', freq='5min')).mean()
    # agg_df["median"] = df.groupby(pd.Grouper(key='time', freq='5min')).median()
    # agg_df["raw"] = df.groupby(pd.Grouper(key='time', freq='5min'))["raw"].apply(list)
    # # Format the time column
    # agg_df.index = agg_df.index.strftime('%H:%m')

    # Group the data into raw values then regroup via aggregation
    # raw_df = df
    # raw_df["raw"] = df.groupby(pd.Grouper(key='time', freq='5min'))["raw"].apply(list)
    df = df.groupby([pd.Grouper(key="time", freq=interval)])["raw"].agg(
        ["mean", "median", "var", "count", "std", "max", "min"]
    )
    logger.info(df)
    # Format the time column
    df.index = df.index.strftime("%H:%M")
    # Crude hack for NaN
    df = df.fillna(0)
    logger.error(df)
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
