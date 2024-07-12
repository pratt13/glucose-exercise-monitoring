import os
import requests
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from constants import BASE_URL, HEADERS
from database_manager import PostgresManager

# Move these user credentials to a DB
load_dotenv(".env.local")

# Logging
# TODO: Properly implement
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="libre.log", format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG
)


class AuthenticationManagement:
    """
    Basic Authentication Class For Libre LinkUp

    Much of this is taken from:
    https://github.com/Daniel-Elston/libre-link/tree/master
    """

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = self.login()

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def login(self, retries=3, delay=60 * 2):
        """Log in to LibreLinkUp and retrieve JWT token."""
        logger.debug("login()")
        endpoint = "/llu/auth/login"
        payload = {"email": self.email, "password": self.password}

        for attempt in range(retries + 1):
            try:
                logger.info(f"Fetching token for {self.email}")
                response = requests.post(BASE_URL + endpoint, headers=HEADERS, json=payload)
                response.raise_for_status()
                data = response.json()
                token = data.get("data", {}).get("authTicket", {}).get("token", {})
                self._expiration_date = datetime.fromtimestamp(
                    data.get("data").get("authTicket", {}).get("expires")
                )
                logger.debug(f"Successfully retrieved token for {self.email}")
                return token
            except requests.exceptions.HTTPError as ex:
                if ex.response.status_code == 429 and attempt < retries:
                    logger.warning(
                        f"Rate limit exceeded, waiting {delay} seconds before retrying..."
                    )
                    time.sleep(delay)
                    continue
                raise ex

    def refresh_token(self, **kwargs):
        """
        Refresh token
        """
        logger.debug("refresh_token()")
        self.token = self.login(**kwargs)

    def get_token(self):
        """
        Get fresh token
        """
        logger.debug("get_token()")
        if datetime.now() >= self._expiration_date + timedelta(minutes=-2):
            self.refresh_token()
        else:
            logger.debug("Using existing token")
        return self.token


class Glucose:
    """
    Simple class to poll data from the LibreLinkUpApp
    """

    def __init__(self, email, password, auth, db_manager):
        # Initialise auth
        self.auth_manager = auth(email, password)
        self.email = email
        self.password = password
        self.patient_ids = self.get_patient_ids()
        self.db_manager = db_manager(
            os.environ["DB_USERNAME"],
            os.environ["DB_PASSWORD"],
            os.environ["DB_HOST"],
            os.environ["DB_NAME"],
        )

    @property
    def patient_ids(self):
        return self._patient_ids

    @patient_ids.setter
    def patient_ids(self, value):
        self._patient_ids = value

    def get_patient_ids(self):
        """
        Retrieve patient IDs from LibreLinkUp.
        """
        logger.info(f"Getting patient ids for email")
        token = self.auth_manager.get_token()
        endpoint = "/llu/connections"
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.get(BASE_URL + endpoint, headers=headers)
        response.raise_for_status()
        patient_data = response.json().get("data", [])
        return [data.get("patientId") for data in patient_data]

    def get_cgm_data(self, patient_id):
        """Retrieve CGM data for a specific patient from LibreLinkUp."""
        logger.info(f"Getting CGM data")
        token = self.auth_manager.get_token()
        endpoint = f"/llu/connections/{patient_id}/graph"
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.get(BASE_URL + endpoint, headers=headers)
        response.raise_for_status()
        resp = response.json()
        logger.debug(f"Response: {resp}")
        logger.debug("Saving to database")
        logger.debug(self.db_manager.conn_params)
        # If no record set really far back
        last_record = self.db_manager.get_last_record()
        last_timestamp, max_id = last_record
        self.db_manager.save_glucose_data(
            self.format_cgm_data(last_timestamp, max_id, resp.get("data").get("graphData"))
        )
        return resp

    @staticmethod
    def format_cgm_data(last_timestamp, max_id, data):
        """
        Get the current data stored in the database
        Filter out any records already in the database
        Return only the not previously recorded data

        :data:
            {'FactoryTimestamp': '7/11/2024 3: 22: 43 AM', 'Timestamp': '7/11/2024 4: 22: 43 AM', 'type': 0, 'ValueInMgPerDl': 80, 'MeasurementColor': 1, 'GlucoseUnits': 0, 'Value': 4.4, 'isHigh': False, 'isLow': False
        """
        logging.info("format_cgm_data()")
        filtered_records = [
            (record.get("Value"), record.get("Timestamp"))
            for record in data
            if (
                datetime.strptime(record.get("Timestamp"), "%d/%m/%Y %H:%M:%S %p") - last_timestamp
            ).seconds
            > 0
        ]
        sorted_records = sorted(
            filtered_records, key=lambda x: datetime.strptime(x[1], "%d/%m/%Y %H:%M:%S %p")
        )
        logging.debug(f"Adding records: {sorted_records}")
        return [
            (idx + max_id + 1, sorted_records[idx][0], sorted_records[idx][1])
            for idx in range(len(sorted_records))
        ]


# Dummy test for refresh
email = os.getenv("LIBRE_EMAIL")
password = os.getenv("LIBRE_PASSWORD")
# postgres_manager = PostgresManager(
#     os.getenv("DB_USERNAME"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_NAME")
# )
g = Glucose(email, password, AuthenticationManagement, PostgresManager)
patient_ids = g.patient_ids
count = 0
while count < 10:
    print(f"Iteration: {count+1}")
    for patient_id in patient_ids:
        g.get_cgm_data(patient_id)
    time.sleep(60 * 1)
    count += 1
