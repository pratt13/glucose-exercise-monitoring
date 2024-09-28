import requests
import logging
from datetime import timedelta


from src.base import Base
from src.constants import DATA_TYPES, STRAVA_BASE_URL, STRAVA_DATETIME, TABLE_SCHEMA
from src.utils import compute_epoch, convert_str_to_ts, convert_ts_to_str


logger = logging.getLogger(__name__)


class Strava(Base):
    def __init__(self, client_id, client_secret, refresh_token, code, db_manager):
        self.client_id = client_id
        self.client_secret = client_secret
        if refresh_token is not None:
            logger.debug("Using provided refresh token via Environment")
            self.refresh_token = refresh_token
        else:
            logger.debug("Generating refresh token via authorization code")
            self.code = code
            self.refresh_token = self.get_refresh_token()
        self.db_manager = db_manager

    @property
    def name(self):
        return "Strava"

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def refresh_token(self):
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value):
        self._refresh_token = value

    def get_refresh_token(self):
        logger.debug("get_refresh_token()")
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": self.code,
            "grant_type": "authorization_code",
        }
        res = requests.post(f"{STRAVA_BASE_URL}/oauth/token", data=payload)
        return res.json().get("refresh_token")

    def get_access_token(self):
        """
        Get Strava Access token
        """
        logger.debug("get_access_token()")
        logger.debug(self.refresh_token)
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        res = requests.post(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        res_json = res.json()
        logger.debug(res_json)
        res.raise_for_status()
        # Get access token and update refresh token
        access_token = res_json.get("access_token")
        self.refresh_token = res_json.get("refresh_token")
        return access_token

    def get_activity_data(self, **kwargs):
        """
        Get the activity data from strava
        Records per page are the number of records to fetch.
        Page is the page from the api to fetch.
        """
        headers = {"Authorization": f"Bearer {self.get_access_token()}"}
        response: dict = requests.get(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers=headers,
            params=kwargs,
        )
        response.raise_for_status()
        activity_data = response.json()
        logger.debug(f"Retrieved {activity_data}")
        return activity_data

    def _save_data(self, data):
        logger.debug(
            f"Saving {len(data)} records into {TABLE_SCHEMA.NAME[DATA_TYPES.STRAVA]}"
        )
        self.db_manager.save_data(data, DATA_TYPES.STRAVA)
        logger.debug(
            f"Successfully saved {len(data)} records into {TABLE_SCHEMA.NAME[DATA_TYPES.STRAVA]}"
        )

    def _get_last_record(self):
        """
        Get the last record's timestamp in the database
        If none present, return the start of time
        """
        logger.debug("_get_last_record()")
        last_record = self.db_manager.get_last_record(DATA_TYPES.STRAVA)
        logger.debug(f"Last record: {last_record}")
        return last_record[0]

    @staticmethod
    def format_activity_data(record):
        # TOOD: VAlidate schema
        start_time = record.get("start_date")
        # Compute - use elapsed time not just moving time in case of breaks/splits
        end_time = convert_ts_to_str(
            convert_str_to_ts(record.get("start_date"), "%Y-%m-%dT%H:%M:%SZ")
            + timedelta(seconds=record.get("elapsed_time", 0)),
            STRAVA_DATETIME,
        )
        default_lat_lang = [0, 0]
        start_latlang = record.get("start_latlng") or default_lat_lang
        end_latlang = record.get("end_latlng") or default_lat_lang
        start_latitude = start_latlang[0]
        end_latitude = end_latlang[0]
        start_longitude = start_latlang[1]
        end_longitude = end_latlang[1]
        fmt_record = {
            "id": record.get("athlete", {}).get("id") + record.get("id"),
            "distance": record.get("distance"),
            "activity_type": record.get("type"),
            "moving_time": record.get("moving_time"),
            "elapsed_time": record.get("elapsed_time"),
            "start_time": start_time,
            "end_time": end_time,
            "start_latitude": start_latitude,
            "end_latitude": end_latitude,
            "start_longitude": start_longitude,
            "end_longitude": end_longitude,
        }
        return fmt_record

    def get_records_between_timestamp(self, start_time, end_time):
        """
        Get the strava data between the end/start times
        """
        logger.debug(f"get_records({start_time}, {end_time})")
        return self._get_records(start_time, end_time)

    def _get_records(self, start_time, end_time):
        logger.debug(f"_get_records({start_time}, {end_time})")
        return self.db_manager.get_records_between_timestamp(
            DATA_TYPES.STRAVA, start_time, end_time
        )

    def update_data(self, records_per_page=1, page=1):
        """
        Get the latest record stored in the database
        Get the latest data from the Strava API from that latest record
        Add any new records to the database
        """
        logger.debug("update_data()")
        last_record = self._get_last_record()
        data = self.get_activity_data(
            after=compute_epoch(last_record),
            records_per_page=records_per_page,
            page=page,
        )
        if data:
            formatted_data = [
                tuple(list(self.format_activity_data(record).values()))
                for record in data
            ]
            self._save_data(formatted_data)
        else:
            logger.debug(
                f"No Strava data to save into {TABLE_SCHEMA.NAME[DATA_TYPES.STRAVA]}"
            )
