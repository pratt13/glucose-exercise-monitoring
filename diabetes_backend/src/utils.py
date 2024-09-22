import os
from datetime import datetime, timedelta
from src.constants import STRAVA_DATETIME, TIME_FMT
import numpy as np
import pandas as pd
from itertools import groupby

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


# These have performance consequences
# 10th Percentile
def q10(x):
    return x.quantile(0.1)


# 25th Percentile
def q25(x):
    return x.quantile(0.25)


# 75th Percentile
def q75(x):
    return x.quantile(0.75)


# 90th Percentile
def q90(x):
    return x.quantile(0.9)


def glucose_quartile_data(data, date_index, glucose_index):
    """
    Bucket the data into intervals
    Compute the quartile data
    For quartile data we do not need additional extrapolation of data
    to include boundary points. We can group all the data between a time interval
    and analyse that.
    """
    logger.debug("glucose_quartile_data()")
    timestamps = list(
        map(lambda x: convert_time_to_str(x[date_index], STRAVA_DATETIME), data)
    )
    glucose_list = list(map(lambda x: float(x[glucose_index]), data))

    df = pd.DataFrame({"time": timestamps, "raw": glucose_list})
    # Convert to dt and replace all the yyy/mm/dd with the same as we only want hours
    # may want to do pd series instead at some point
    df["time"] = pd.to_datetime(df["time"]).apply(
        lambda t: t.replace(day=31, year=2000, month=12)
    )

    df = df.groupby([pd.Grouper(key="time", freq="15min")])["raw"].agg(
        ["median", "max", "min", q10, q25, q75, q90]
    )
    # Format the time column
    df.index = df.index.strftime("%H:%M")
    # Crude hack for NaN
    df = df.fillna(0)
    return {
        "intervals": list(df.index.values),
        "medianValues": df["median"].to_list(),
        "maxValues": df["max"].to_list(),
        "minValues": df["min"].to_list(),
        "q10": df["q10"].to_list(),
        "q25": df["q25"].to_list(),
        "q75": df["q75"].to_list(),
        "q90": df["q90"].to_list(),
    }


def glucose_moment_data(data, date_index, glucose_index):
    """
    Bucket the data into 15minute intervals and compute the moments
    """
    logger.debug("glucose_moment_data()")
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

    df = df.groupby([pd.Grouper(key="time", freq="15min")])["raw"].agg(
        ["mean", "median", "var", "count", "std", "max", "min", q10, q25, q75, q90]
    )
    # Format the time column
    df.index = df.index.strftime("%H:%M")
    # Crude hack for NaN
    df = df.fillna(0)
    return {
        "intervals": list(df.index.values),
        "meanValues": df["mean"].to_list(),
        "numRecords": df["count"].to_list(),
        "varValues": df["var"].to_list(),
        "stdValues": df["std"].to_list(),
        "maxValues": df["max"].to_list(),
        "minValues": df["min"].to_list(),
    }


def aggregate_glucose_data(data, date_index, glucose_index, bucket="15min"):
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
        df.groupby([pd.Grouper(key="time", freq=bucket)])["raw"].apply(list).to_list()
    )
    # # Low levels,
    # lows = (
    #     df.groupby([pd.Grouper(key="time", freq=interval)])["raw"].agg()
    # )

    df = df.groupby([pd.Grouper(key="time", freq=bucket)])["raw"].agg(
        ["mean", "median", "var", "count", "std", "max", "min", q10, q25, q75, q90]
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
        "q10": df["q10"].to_list(),
        "q25": df["q25"].to_list(),
        "q75": df["q75"].to_list(),
        "q90": df["q90"].to_list(),
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


def libre_hba1c(data, timestamp_index, glucose_index):
    """
    Computing the HBA1C
    """
    logger.debug("libre_hba1c()")

    if len(data) < 2:
        return {"hBA1C": None}

    # Order (in time order) and extract the data
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    timestamp_list = list(map(lambda x: x[timestamp_index], ordered_data))
    glucose_list = list(map(lambda x: float(x[glucose_index]), ordered_data))

    # Running count for the seconds low/high
    total_seconds = (timestamp_list[-1] - timestamp_list[0]).total_seconds()

    # Check the date range spans an hour, else exit early
    if total_seconds < 60 * 60:
        return {"hBA1C": None}

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
    logger.debug("Finished computing HBA1C")
    return {
        "hBA1C": mean,
    }


def compute_percentages(  # noqa: C901
    data, interval_length_seconds=3600, high=10, low=4
):
    """
    Computing the percentage of time below/above a threshold
    Assumes the last record and the first record is the span of the window
    """
    if high <= low:
        raise ValueError(f"Cannot specify the high value {high} <= low value {low}")

    # If there is no data or one record then exit early
    if len(data) == 0:
        return {
            "percentageOfTimeInTarget": None,
            "percentageOfTimeLow": None,
            "percentageOfTimeHigh": None,
            "numberOfHighs": None,
            "numberOfLows": None,
        }
    elif len(data) == 1:
        _, glucose = data[0]
        is_low = glucose < low
        is_high = glucose > high
        return {
            "percentageOfTimeInTarget": 100 if not is_low and not is_high else 0,
            "percentageOfTimeLow": 100 if is_low else 0,
            "percentageOfTimeHigh": 100 if is_high else 0,
            "numberOfHighs": int(is_high),
            "numberOfLows": int(is_low),
        }

    timestamp_list, glucose_list = zip(*data)

    # Running count for the seconds low/high
    total_high_seconds = 0
    total_low_seconds = 0

    last_glucose = glucose_list[0]
    last_time = timestamp_list[0]

    # Set the last transition time
    transition_into_extreme = last_time

    # Running count of number of highs
    # Initial event must be counted if high/low
    number_of_highs = 1 if last_glucose >= high else 0
    number_of_lows = 1 if last_glucose <= low else 0

    for cur_glucose, cur_time in zip(glucose_list[1:], timestamp_list[1:]):
        if cur_glucose >= high and last_glucose < high:
            # Changing into high region
            transition_into_extreme = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), high
            )
            number_of_highs += 1
        elif cur_glucose < high and last_glucose >= high:
            # transitioning out of high region
            transition_time = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), high
            )
            total_high_seconds += (
                transition_time - transition_into_extreme
            ).total_seconds()
        elif cur_glucose <= low and last_glucose > low:
            # Transitioning into low
            transition_into_extreme = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), low
            )
            number_of_lows += 1
        elif cur_glucose > low and last_glucose <= low:
            # Transitioning out
            transition_time = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), low
            )
            total_low_seconds += (
                transition_time - transition_into_extreme
            ).total_seconds()

        # Update the last record processed
        last_glucose = cur_glucose
        last_time = cur_time

    # Edge case at the the end
    # If the last value is high/low need to include that in the statistics
    if last_glucose >= high:
        total_high_seconds += (
            timestamp_list[-1] - transition_into_extreme
        ).total_seconds()
    elif last_glucose <= low:
        total_low_seconds += (
            timestamp_list[-1] - transition_into_extreme
        ).total_seconds()

    return {
        "numberOfHighs": number_of_highs,
        "numberOfLows": number_of_lows,
        "percentageOfTimeHigh": round(
            (total_high_seconds / interval_length_seconds) * 100, 2
        ),
        "percentageOfTimeLow": round(
            (total_low_seconds / interval_length_seconds) * 100, 2
        ),
        "percentageOfTimeInTarget": round(
            (
                (interval_length_seconds - total_low_seconds - total_high_seconds)
                / interval_length_seconds
            )
            * 100,
            2,
        ),
    }


def libre_glucose_percentages(data, timestamp_index, glucose_index, high=10, low=4):
    """
    Computing the percentage of time below/above
    """
    logger.debug(f"libre_glucose_percentages() with targets {high}-{low}")
    # Order (in time order) and extract the data
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    timestamp_list = list(map(lambda x: x[timestamp_index], ordered_data))
    glucose_list = list(map(lambda x: float(x[glucose_index]), ordered_data))

    # Running count for the seconds low/high
    total_seconds = (timestamp_list[-1] - timestamp_list[0]).total_seconds()
    total_high_seconds = 0
    total_low_seconds = 0

    if total_seconds < 60 * 60 * 12:
        logger.debug(f"Not a long enough time window {total_seconds/(60*60)} hours")
        # Not enough data
        return {
            "percentageOfTimeInTarget": None,
            "percentageOfTimeLow": None,
            "percentageOfTimeHigh": None,
            "numberOfHighs": None,
            "numberOfLows": None,
        }

    last_glucose = glucose_list[0]
    last_time = timestamp_list[0]

    new_data = []
    # Set the last transition time
    last_transition_time = last_time

    # Running count of number of highs
    number_of_highs = 1 if last_glucose >= high else 0
    number_of_lows = 1 if last_glucose <= low else 0

    for cur_glucose, cur_time in zip(glucose_list[1:], timestamp_list[1:]):
        if (cur_glucose >= high and last_glucose < high) or (
            cur_glucose < high and last_glucose >= high
        ):
            # Just changing into it, or out of it, compute the x value of the
            # transition using a linear relationship
            x = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), high
            )
            # If moving into high just set the last_transition_time
            if cur_glucose >= high and last_glucose < high:
                last_transition_time = cur_time.replace(
                    second=0, hour=0, minute=0
                ) + timedelta(seconds=x)
                number_of_highs += 1
            else:
                total_high_seconds += (cur_time - last_transition_time).total_seconds()
            # Add the data
            # TODO: Not strictly needed, can remove
            new_data.append(
                [
                    high,
                    cur_time.replace(second=0, hour=0, minute=0) + timedelta(seconds=x),
                ]
            )
        elif (cur_glucose <= low and last_glucose > low) or (
            cur_glucose > low and last_glucose <= low
        ):
            # Just changing into it, or out of it, compute the x value of the
            # transition using a linear relationship
            x = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), low
            )
            # If moving into low just set the last_transition_time
            if cur_glucose <= low and last_glucose > low:
                last_transition_time = cur_time.replace(
                    second=0, hour=0, minute=0
                ) + timedelta(seconds=x)
                number_of_lows += 1
            else:
                total_low_seconds += (cur_time - last_transition_time).total_seconds()
            new_data.append(
                [
                    low,
                    cur_time.replace(second=0, hour=0, minute=0) + timedelta(seconds=x),
                ]
            )

        # Update the last record processed
        last_glucose = cur_glucose
        last_time = cur_time

    # Edge case at the the end
    # If the last value is high/low need to include that in the statistics
    if last_glucose > high:
        total_high_seconds += (last_time - last_transition_time).total_seconds()
    elif last_glucose < low:
        total_low_seconds += (last_time - last_transition_time).total_seconds()

    return {
        "percentageOfTimeInTarget": 100
        * (total_seconds - total_high_seconds - total_low_seconds)
        / total_seconds,
        "percentageOfTimeLow": 100 * total_low_seconds / total_seconds,
        "percentageOfTimeHigh": 100 * total_high_seconds / total_seconds,
        "numberOfHighs": number_of_highs,
        "numberOfLows": number_of_lows,
    }


def libre_extremes_in_buckets(
    data, timestamp_index, glucose_index, high=10, low=4, bucket="15min"
):
    """
    Computing in time buckets the time in target and number of lows

    """
    logger.debug(
        f"libre_glucose_percentages() with targets {high}-{low} and buckets: {bucket}"
    )
    logger.debug(f"Checking {len(data)} records")
    # Order (in time order) and extract the data
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    timestamp_list = list(map(lambda x: x[timestamp_index], ordered_data))
    glucose_list = list(map(lambda x: float(x[glucose_index]), ordered_data))

    # Find the total seconds being computed
    total_seconds = (timestamp_list[-1] - timestamp_list[0]).total_seconds()

    if total_seconds < 60 * 60 * 12:
        logger.debug(f"Not a long enough time window {total_seconds/(60*60)} hours")
        # Not enough data
        return {
            "percentageOfTimeInTarget": None,
            "percentageOfTimeLow": None,
            "percentageOfTimeHigh": None,
            "numberOfHighs": None,
            "numberOfLows": None,
        }

    # Find the intervals going to be defined
    # Then populate the boundaries
    intervals = list(
        pd.DataFrame(
            {
                "timestamp": [timestamp_list[0], timestamp_list[-1]],
                "value": [0, 1],
            }
        )
        .groupby([pd.Grouper(key="timestamp", freq=bucket)])
        .groups.keys()
    )
    last_timestamp = timestamp_list[0]
    last_glucose = glucose_list[0]
    current_interval_index = 1
    enriched_data = list(zip(timestamp_list, glucose_list))
    for timestamp, glucose in zip(timestamp_list[1:], glucose_list[1:]):
        current_interval = intervals[current_interval_index]
        if (current_interval - last_timestamp).total_seconds() > 0 and (
            timestamp - current_interval
        ).total_seconds() > 0:
            # neither points are zero else they are boundary points
            _, new_y_data_point = compute_y_value_with_x_time(
                (last_timestamp, last_glucose),
                (timestamp, glucose),
                (current_interval - last_timestamp).total_seconds() / 60,
            )
            # increment running values
            current_interval_index += 1
            last_timestamp = current_interval
            last_glucose = glucose
            # Add new data points
            enriched_data.append(
                (current_interval - timedelta(seconds=1), new_y_data_point)
            )
            enriched_data.append((current_interval, new_y_data_point))

            if current_interval_index == len(intervals):
                # Exit everything has now fallen into the last bucket nothing else to process
                break

    ordered_enriched_data = sorted(enriched_data, key=lambda x: x[0])
    enriched_timestamp_list, enriched_glucose_list = list(zip(*ordered_enriched_data))

    # Create a pandas df
    df = pd.DataFrame(
        {
            "timestamp": enriched_timestamp_list,
            "glucose": enriched_glucose_list,
        }
    )

    # Group the data into buckets and store as a list of tuple records
    df3 = (
        df.groupby([pd.Grouper(key="timestamp", freq=bucket)])
        .apply(lambda x: [(t, g) for t, g in zip(x["timestamp"], x["glucose"])])
        .apply(list)
    )
    records = []
    for group, grouped_data in df3.items():
        records.append(
            {
                "timeInterval": group.strftime(STRAVA_DATETIME),
                "timeIntervalData": compute_percentages(
                    grouped_data,
                    interval_length_seconds=get_seconds_from_pandas_interval(bucket),
                    high=high,
                    low=low,
                ),
            }
        )

    return records


def libre_data_bucketed_day_overview(
    data, timestamp_index, glucose_index, high=10, low=4, bucket="15min"
):
    """
    Bucket the data in intervals and compute metrics upon it
    Then take those day buckets and combine them, so monday 12-13 is joined with tuesday 12-13 etc
    """
    records = libre_extremes_in_buckets(
        data, timestamp_index, glucose_index, high=high, low=low, bucket=bucket
    )

    # Replace the year of each time stamp
    fmt_records = sorted(
        [
            {
                **record,
                "timeInterval": convert_ts_to_str(
                    convert_str_to_ts(record["timeInterval"], STRAVA_DATETIME).replace(
                        year=2000, month=1, day=1
                    ),
                    TIME_FMT,
                ),
            }
            for record in records
        ],
        key=lambda x: x.get("timeInterval"),
    )
    agg_data = []
    for time_interval, grouped_records in groupby(
        fmt_records, key=lambda x: x.get("timeInterval")
    ):
        list_grouped_records = list(grouped_records)
        num_grouped_records = len(list_grouped_records)
        # Make this more readable
        # Normalise some
        # Handle Nones
        agg_record = {
            key: sum(
                sub_rec["timeIntervalData"][key] or 0
                for sub_rec in list_grouped_records
            )
            / (num_grouped_records if "percent" in key else 1)
            for key in list_grouped_records[0]["timeIntervalData"].keys()
        }
        agg_data.append({"timeInterval": time_interval, "timeIntervalData": agg_record})

    return agg_data


def get_seconds_from_pandas_interval(interval):
    if "min" in interval:
        return int(interval.replace("min", "")) * 60
    else:
        raise NotImplementedError


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
    if len(data) < 2:
        # Not enough data
        return {
            "raw_data": [],
            "meta_data": {
                "percentage_of_time_in_target": None,
                "percentage_of_time_low": None,
                "percentage_of_time_high": None,
                "number_highs": None,
                "number_lows": None,
                "mean": None,
                "st_dev": None,
            },
        }
    # Order (in time order) and extract the data
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    timestamp_list = list(map(lambda x: x[timestamp_index], ordered_data))
    glucose_list = list(map(lambda x: float(x[glucose_index]), ordered_data))
    last_glucose = glucose_list[0]
    last_time = timestamp_list[0]
    new_data = []
    # Set the last transition time
    last_transition_time = last_time

    # Running count for the seconds low/high
    total_seconds = (timestamp_list[-1] - timestamp_list[0]).total_seconds()
    total_high_seconds = 0
    total_low_seconds = 0

    # Running count of number of highs
    number_of_highs = 1 if last_glucose >= high else 0
    number_of_lows = 1 if last_glucose <= low else 0

    for cur_glucose, cur_time in zip(glucose_list[1:], timestamp_list[1:]):
        if (cur_glucose >= high and last_glucose < high) or (
            cur_glucose < high and last_glucose >= high
        ):
            # Just changing into it, or out of it, compute the x value of the
            # transition using a linear relationship
            x = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), high
            )
            # If moving into high just set the last_transition_time
            if cur_glucose >= high and last_glucose < high:
                last_transition_time = cur_time.replace(
                    second=0, hour=0, minute=0
                ) + timedelta(seconds=x)
                number_of_highs += 1
            else:
                total_high_seconds += (cur_time - last_transition_time).total_seconds()
            # Add the data
            # TODO: Not strictly needed, can remove
            new_data.append(
                [
                    high,
                    cur_time.replace(second=0, hour=0, minute=0) + timedelta(seconds=x),
                ]
            )
        elif (cur_glucose <= low and last_glucose > low) or (
            cur_glucose > low and last_glucose <= low
        ):
            # Just changing into it, or out of it, compute the x value of the
            # transition using a linear relationship
            x = compute_x_time_value(
                (last_time, last_glucose), (cur_time, cur_glucose), low
            )
            # If moving into low just set the last_transition_time
            if cur_glucose <= low and last_glucose > low:
                last_transition_time = cur_time.replace(
                    second=0, hour=0, minute=0
                ) + timedelta(seconds=x)
                number_of_lows += 1
            else:
                total_low_seconds += (cur_time - last_transition_time).total_seconds()
            new_data.append(
                [
                    low,
                    cur_time.replace(second=0, hour=0, minute=0) + timedelta(seconds=x),
                ]
            )

        # Update the last record processed
        last_glucose = cur_glucose
        last_time = cur_time

    # Edge case at the the end
    # If the last value is high/low need to include that in the statistics
    if last_glucose > high:
        total_high_seconds += (last_time - last_transition_time).total_seconds()
    elif last_glucose < low:
        total_low_seconds += (last_time - last_transition_time).total_seconds()

    # Add new data
    # expanded_data = sorted(
    #     list(zip(glucose_list, timestamp_list)) + new_data, key=lambda x: x[1]
    # )
    # new_glucose_list, _ = zip(*expanded_data)

    # # Naive solution - pandas groupby must work or something similar
    # is_low = expanded_data[0][0] < low
    # is_high = expanded_data[0][0] > high
    # last_time = (
    #     None
    #     if expanded_data[0][0] > high or expanded_data[0][0] < low
    #     else expanded_data[0][1]
    # )
    # for gluc, time in expanded_data[1:]:
    #     if is_low and gluc >= low and gluc <= high:
    #         total_low_seconds += (time - last_time).total_seconds()
    #         is_low = False
    #         last_time = time
    #     elif is_high and gluc >= low and gluc <= high:
    #         total_high_seconds += (time - last_time).total_seconds()
    #         is_high = False
    #         last_time = time
    #     elif gluc < low:
    #         is_low = True
    #         last_time = time
    #     elif gluc > high:
    #         is_high = True
    #         last_time = time

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
        "rawData": list(zip(glucose_list, timestamp_list)),
        "metaData": {
            "percentageOfTimeInTarget": 100
            * (total_seconds - total_high_seconds - total_low_seconds)
            / total_seconds,
            "percentageOfTimeLow": 100 * total_low_seconds / total_seconds,
            "percentageOfTimeHigh": 100 * total_high_seconds / total_seconds,
            "numberOfHighs": number_of_highs,
            "numberOfLows": number_of_lows,
            "mean": mean,
            "stDev": np.sqrt(df["st_dev_pre_calc"].sum() / n),
        },
    }


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
    if (x2 - x1).total_seconds() < 0:
        raise ValueError(f"Cannot have the second point {x2} before the first {x1}")
    # New position
    new_x = x1 + timedelta(minutes=target_x_value_mins)
    if y1 == y2:
        # Same value, zero gradient
        return [new_x, y1]
    epoch_time = datetime(1970, 1, 1, 0, 0, 0)
    m = (y2 - y1) / ((x2 - x1).total_seconds())
    c = y2 - (m * (x2 - epoch_time)).total_seconds()
    new_x = x1 + timedelta(minutes=target_x_value_mins)
    return [new_x, round(((new_x - epoch_time).total_seconds() * m) + c, 2)]


def compute_x_time_value(pos1, pos2, target_y_value):
    """
    Given time series data along the x axis, find a missing point between
    two points, where y = target_y_value
    """
    x1, y1 = pos1
    x2, y2 = pos2
    if (x2 - x1).total_seconds() < 0:
        raise ValueError(f"Cannot have the second point {x2} before the first {x1}")
    if y1 == y2:
        raise ValueError(
            f"Cannot compute the time that the y value {target_y_value} is reached if the gradient is zero"
        )
    start_of_x2 = x2.replace(second=0, hour=0, minute=0)
    m = (y2 - y1) / ((x2 - x1).total_seconds())
    c = y2 - (m * (x2 - start_of_x2).total_seconds())
    time_in_seconds_since_day_start = (target_y_value - c) / m
    return start_of_x2 + timedelta(seconds=time_in_seconds_since_day_start)


def compute_time_bucketed_metrics(data, timestamp_index, glucose_index, high=10, low=4):
    """
    TODO:
    Get the raw data,
        * add a column for high, +1 if goes from normal to high
        * add a column for low, +1 if goes from normal to high
    Group the data by hours
    """
    # Unpack the data - don't use zip unless we know the structure instead use index
    # As its ordered we can remove the day data now, but instead just first day of the
    # millenium
    # TODO: Format to time only
    ordered_data = sorted(data, key=lambda x: x[timestamp_index])
    total_days = int(
        (
            ordered_data[0][timestamp_index] - ordered_data[-1][timestamp_index]
        ).total_seconds()
        / (60 * 60 * 24)
    )
    logger.info(f"Total days in range {total_days}")
    timestamp_list = list(
        map(
            lambda x: x[timestamp_index].replace(year=2000, day=1, month=1),
            ordered_data,
        )
    )
    glucose_list = list(map(lambda x: float(x[glucose_index]), ordered_data))

    # Create a DataFrame
    df = pd.DataFrame({"timestamp": timestamp_list, "glucose": glucose_list})

    # calculate the time difference between consecutive rows
    # DO one iteration if no pandas way with apply
    df["new_high"] = [1 if glucose_list[0] >= high else 0] + [
        cur_gluc >= high and glucose_list[idx - 1] < high
        for idx, cur_gluc in enumerate(glucose_list[1:], start=1)
    ]
    df["new_low"] = [1 if glucose_list[0] <= low else 0] + [
        cur_gluc <= low and glucose_list[idx - 1] > high
        for idx, cur_gluc in enumerate(glucose_list[1:], start=1)
    ]
    # Groupby
    # TODO: One operation?
    df["num_highs"] = df.groupby([pd.Grouper(key="timestamp", freq="1H")])[
        "new_high"
    ].agg(["count"])
    df["num_lows"] = df.groupby([pd.Grouper(key="timestamp", freq="1H")])[
        "new_low"
    ].agg(["count"])
    dfagg = df.groupby([pd.Grouper(key="timestamp", freq="1H")])["glucose"].agg(
        ["mean", "median", "var", "count", "std", "max", "min"]
    )

    return {
        "data": ordered_data,
        "agg": {
            "intervals": list(df.index.values),
            "count_lows": df["num_lows"].to_list(),
            "count_highs": df["num_highs"].to_list(),
            "mean": dfagg["mean"].to_list(),
            "count_events": dfagg["count"].to_list(),
            "median": dfagg["median"].to_list(),
            "var": dfagg["var"].to_list(),
            "std": dfagg["std"].to_list(),
            "max": dfagg["max"].to_list(),
            "min": dfagg["min"].to_list(),
        },
    }
