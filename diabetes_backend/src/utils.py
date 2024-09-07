import os
from datetime import datetime, timedelta
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


def raw_libre_data_analysis(data, timestamp_index, glucose_index, high=10, low=4):
    """
    Computing the percentage of time below/above need to find the line that intercepts
    the data.
    So add artifical points as linear lines between the data.
    For example,
    [5.5,4.1, 3.8, 3.6,4.1] -> [5.5, 4.1, 4.0, 3.8, 3.6, 4.0, 4.1] with the timestamp
    a linear line between them.



    DUPLICAT CODE
    USE DF


    """
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    timestamp_list = list(map(lambda x: x[timestamp_index], ordered_data))
    glucose_list = list(map(lambda x: float(x[glucose_index]), ordered_data))
    last_glucose = glucose_list[0]
    last_time = timestamp_list[0]
    new_data = []
    for cur_glucose, cur_time in zip(glucose_list[1:], timestamp_list[1:]):
        if (cur_glucose > high and last_glucose < high) or (
            cur_glucose < high and last_glucose > high
        ):
            # Just changing into it, or out of it
            x = compute_x_time_value(
                (last_time, cur_time), (cur_time, cur_glucose), high
            )
            new_data.append(
                [
                    high,
                    cur_time.replace(second=0, hour=0, minute=0) + timedelta(seconds=x),
                ]
            )
        elif (cur_glucose < low and last_glucose > low) or (
            cur_glucose > low and last_glucose < low
        ):
            # Just changing into it, or out of it
            x = compute_x_time_value(
                (last_time, cur_time), (cur_time, cur_glucose), low
            )
            new_data.append(
                [
                    low,
                    cur_time.replace(second=0, hour=0, minute=0) + timedelta(seconds=x),
                ]
            )

        last_glucose = cur_glucose
        last_time = cur_time

    # Add new data
    expanded_data = sorted(
        list(zip(glucose_list, timestamp_list)) + new_data, key=lambda x: x[1]
    )
    new_glucose_list, _ = zip(*expanded_data)

    total_seconds = (timestamp_list[-1] - timestamp_list[0]).total_seconds()
    total_high_seconds = 0
    total_low_seconds = 0

    # Naive solution - pandas groupby must work or something similar
    is_low = expanded_data[0][0] < low
    is_high = expanded_data[0][0] > high
    last_time = (
        None
        if expanded_data[0][0] > high or expanded_data[0][0] < low
        else expanded_data[0][1]
    )
    for gluc, time in expanded_data[1:]:
        if is_low and gluc >= low and gluc <= high:
            total_low_seconds += (time - last_time).total_seconds()
            is_low = False
            last_time = time
        elif is_high and gluc >= low and gluc <= high:
            total_high_seconds += (time - last_time).total_seconds()
            is_high = False
            last_time = time
        elif gluc < low:
            is_low = True
            last_time = time
        elif gluc > high:
            is_high = True
            last_time = time

    # Blah
    # create a sample DataFrame
    df = pd.DataFrame({"timestamp": timestamp_list, "glucose": glucose_list})

    # calculate the time difference between consecutive rows
    df["time_diff"] = df["timestamp"].diff()
    # replace missing values with a default value
    df["time_diff"] = df["time_diff"].fillna(pd.Timedelta(seconds=0))
    df["time_diff"] = list(map(lambda x: x.total_seconds(), df["time_diff"]))

    df["glucose_diff"] = df["glucose"].rolling(2).mean()
    df["rolling_mean"] = list(
        map(
            lambda x, y: 0 if x == 0 else abs(y) * (x / total_seconds),
            df["time_diff"],
            df["glucose_diff"],
        )
    )
    mean = df["rolling_mean"].sum()
    df["st_dev_pre_calc"] = list(map(lambda x: (x - mean) ** 2, df["glucose"]))
    n = len(glucose_list)

    # Compute the median value, the mean and the standard deviation
    # Create a pandas dataframe that fills the data into 5 minute intervals if wider than 5.
    # new_data = populate_glucose_data(expanded_data)

    return {
        "raw_data": expanded_data,
        "meta_data": {
            "percentage_of_time_in_target": 100
            * (total_seconds - total_high_seconds - total_low_seconds)
            / total_seconds,
            "percentage_of_time_low": 100 * total_low_seconds / total_seconds,
            "percentage_of_time_high": 100 * total_high_seconds / total_seconds,
            "number_highs": (new_glucose_list.count(high) // 2)
            + (new_glucose_list.count(high) % 2),
            "number_lows": (new_glucose_list.count(low) // 2)
            + (new_glucose_list.count(low) % 2),
            "mean": mean,
            "st_dev": np.sqrt(df["st_dev_pre_calc"].sum() / n),
        },
    }


def compute_non_standard_time_series_stats(data):
    first_glucose, first_time = data[0]
    prev_glucose = first_glucose
    prev_time = first_time
    _last_glucose, last_time = data[-1]
    # _new_data = []
    mean = 0
    # _total_seconds = (last_time - first_time).total_seconds()
    for cur_glucose, cur_time in data[1:]:
        mean += abs(cur_glucose - prev_glucose) / (cur_time - prev_time).total_seconds()


def populate_glucose_data(data, min_interval=5):
    """
    Populate missing data using a linear assumption between consecutive points.
    """
    last_glucose, last_time = data[0]
    new_data = []
    for cur_glucose, cur_time in data[1:]:
        if (cur_time - last_time).total_seconds() > min_interval * 60:
            last_glucose = cur_glucose
            last_time = cur_time
            continue
        new_time, new_glucose = compute_y_value_with_x_time(
            (last_time, last_glucose),
            (cur_time, cur_glucose),
            target_x_value_mins=min_interval,
        )
        new_data.append([new_glucose, new_time])
        # Update the last glucose
        last_time = new_time
        last_glucose = new_glucose

    sorted_data = sorted(data + new_data, key=lambda x: x[1])
    return sorted_data


def compute_y_value_with_x_time(pos1, pos2, target_x_value_mins=5):
    x1, y1 = pos1
    x2, y2 = pos2
    m = (y2 - y1) / ((x2 - x1).total_seconds())
    c = y1 - (m * (x2 - x1.replace(second=0, hour=0, minute=0)).total_seconds())
    new_x = x1 + timedelta(minutes=target_x_value_mins)
    return [new_x, (new_x * m) + c]


def compute_x_time_value(pos1, pos2, target_y_value):
    """
    Given time series data along the x axis, find a missing point between
    two points, where y = target_y_value
    """
    x1, y1 = pos1
    x2, y2 = pos2
    m = (y2 - y1) / ((x2 - x1).total_seconds())
    c = y2 - (m * (x2 - x1.replace(second=0, hour=0, minute=0)).total_seconds())
    return (target_y_value - c) / m
