import os
from datetime import datetime


def compute_epoch(ts, fmt):
    # utc_time = datetime.strptime(ts, fmt)
    return (ts - datetime(1970, 1, 1)).total_seconds()


def convert_str_to_ts(ts, fmt):
    return datetime.strptime(ts, fmt)


def load_libre_credentials_from_env():
    return (os.getenv("LIBRE_EMAIL"), os.getenv("LIBRE_PASSWORD"))


def load_strava_credentials_from_env():
    return (
        os.getenv("STRAVA_CLIENT_ID"),
        os.getenv("STRAVA_CLIENT_SECRET"),
        os.getenv("STRAVA_REFRESH_TOKEN"),
    )


def load_credentials_from_env():
    return {**load_strava_credentials_from_env(), **load_libre_credentials_from_env()}
