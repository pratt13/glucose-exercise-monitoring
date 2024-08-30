BASE_URL = "https://api.libreview.io"
HEADERS = {
    "accept-encoding": "gzip",
    "cache-control": "no-cache",
    "connection": "Keep-Alive",
    "content-type": "application/json",
    "product": "llu.android",
    "version": "4.7",
}
DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p"
STRAVA_DATETIME = "%Y-%m-%d %H:%M:%S"
TIME_FMT = "%H:%M:%S"
DATABASE_DATETIME = STRAVA_DATETIME
DATABASE_TABLE = "glucose_times"
STRAVA_BASE_URL = "https://www.strava.com"
STRAVA_ACTIVITIES_COLUMNS = (
    "id",
    "start_latitude",
    "end_latitude",
    "start_longitude",
    "end_longitude",
    "distance",
    "activity_type",
    "moving_time",
    "elapsed_time",
    "start_time",
    "end_time",
)


# TODO: Must be a nicer way
class DATA_TYPES:

    STRAVA = "STRAVA"
    LIBRE = "LIBRE"
    STRAVA_LIBRE = "STRAVA_LIBRE"


class TABLE_SCHEMA:
    NAME = {
        DATA_TYPES.STRAVA: "activities",
        DATA_TYPES.LIBRE: "glucose_times",
        DATA_TYPES.STRAVA_LIBRE: "strava_libre",
    }
    COLUMNS = {
        DATA_TYPES.STRAVA: [
            "id",
            "distance",
            "activity_type",
            "moving_time",
            "elapsed_time",
            "start_time",
            "end_time",
            "start_latitude",
            "end_latitude",
            "start_longitude",
            "end_longitude",
        ],
        DATA_TYPES.LIBRE: ["id", "glucose", "timestamp"],
        DATA_TYPES.STRAVA_LIBRE: [
            "id",
            "strava_id",
            "libre_id",
            "glucose",
            "timestamp",
        ],
    }
    SEARCH_COLUMNS = {
        DATA_TYPES.STRAVA: ["start_time"],
        DATA_TYPES.LIBRE: ["timestamp", "id"],
        DATA_TYPES.STRAVA_LIBRE: ["timestamp", "id"],
    }
    INDEX_FIELD = {
        DATA_TYPES.STRAVA: "id",
        DATA_TYPES.LIBRE: "id",
        DATA_TYPES.STRAVA_LIBRE: "id",
    }
    TIME_FIELD = {
        DATA_TYPES.STRAVA: "start_time",
        DATA_TYPES.LIBRE: "timestamp",
        DATA_TYPES.STRAVA_LIBRE: "timestamp",
    }
    ORDER_BY = {
        DATA_TYPES.STRAVA: "id",
        DATA_TYPES.LIBRE: "timestamp",
        DATA_TYPES.STRAVA_LIBRE: "timestamp",
    }
