import os
import requests
import logging


from constants import DATA_TYPES, STRAVA_BASE_URL


logger = logging.getLogger(__name__)


class Strava:
    def __init__(self, client_id, client_secret, refresh_token, db_manager):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.db_manager = db_manager(
            os.environ["DB_USERNAME"],
            os.environ["DB_PASSWORD"],
            os.environ["DB_HOST"],
            os.environ["DB_NAME"],
        )

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

    # def get_refresh_token(self):
    #     logger.debug("get_refresh_token()")
    #     payload = {"client_id": self.client_id, "client_secret":self.client_secret, "code":self.code, "grant_type":"authorization_code"}
    #     res = requests.post(f"{STRAVA_BASE_URL}/oauth/token", headers=STRAVA_HEADERS, data=payload)
    #     # self.token = res
    #     payload = {
    #         "client_id": self.client_id,
    #         "client_secret": self.client_secret,
    #         "refresh_token": self.refresh_token,
    #         "grant_type": "refresh_token",
    #         "f": "json",
    #     }
    #     res = requests.post("https://www.strava.com/oauth/token", data=payload, verify=False)
    #     access_token = res.json().get("access_token")
    #     return access_token

    def get_token(self):
        """
        Get Strava Access token
        """
        logger.debug("get_token()")
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        res = requests.post(f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False)
        access_token = res.json().get("access_token")
        return access_token

    def get_activity_data(self, records_per_page=1, page=1):
        """
        Get the activity data from strava
        Records per page are the number of records to fetch.
        Page is the page from the api to fetch.
        """
        headers = {"Authorization": f"Authorization: Bearer {self.get_token()}"}
        response: dict = requests.get(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers=headers,
            params={"per_page": records_per_page, "page": page},
        )
        response.raise_for_status()
        activity_data = response.json()
        return activity_data

    def _save_data(self, data):
        logger.debug("_save_data()")
        self.db_manager.save_data(data, DATA_TYPES.STRAVA)

    @staticmethod
    def _format_activity_data(record):
        # TOOD: VAlidate schema
        start_time = record.get("start_date")
        # Compute
        end_time = record.get("start_date")
        fmt_record = {
            "id": record.get("athlete", {}).get("id") + record.get("id"),
            "distance": record.get("distance"),
            "activity_type": record.get("type"),
            "moving_time": record.get("moving_time"),
            "elapsed_time": record.get("elapsed_time"),
            "start_time": start_time,
            "end_time": end_time,
            "start_latitude": record.get("start_latlng")[0],
            "end_latitude": record.get("end_latlng")[0],
            "start_longitude": record.get("start_latlng")[1],
            "end_longitude": record.get("end_latlng")[1],
        }
        logger.debug(f"Formatted Record: {fmt_record}")
        return fmt_record

    def update_data(self, records_per_page=1, page=1):
        """
        Get the latest record stored in the database
        Get the latest data from the Strava API from that latest record
        Add any new records to the database
        """
        logger.debug("update_data()")
        # # data = self.get_activity_data(records_per_page=records_per_page, page=page)
        # formatted_data = [list(self._format_activity_data(record).values()) for record in data]
        formatted_data = {
            "id": 11889253225,
            "distance": 7445.9,
            "activity_type": "Run",
            "moving_time": 2604,
            "elapsed_time": 2731,
            "start_time": "2024-07-14T08:47:01Z",
            "end_time": "2024-07-14T08:47:01Z",
            "start_latitude": 51.308409590274096,
            "end_latitude": 51.30836768075824,
            "start_longitude": -2.5024617835879326,
            "end_longitude": -2.5024617835879326,
        }
        logger.debug("******************")
        logger.debug([str(v) for v in list(formatted_data.values())])
        logger.debug(
            [
                tuple([str(v) for v in list(formatted_data.values())]),
                tuple([str(v) for v in list(formatted_data.values())]),
            ]
        )
        self._save_data([tuple([str(v) for v in list(formatted_data.values())])])
