from datetime import datetime


def compute_epoch(ts, fmt):
    # utc_time = datetime.strptime(ts, fmt)
    return (ts - datetime(1970, 1, 1)).total_seconds()
