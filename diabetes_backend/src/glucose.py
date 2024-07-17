import os
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

from constants import BASE_URL, HEADERS, DATETIME_FORMAT
from database_manager import PostgresManager
from auth import AuthenticationManagement

# Environment variables - default to non-docker patterns
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "glucose.log")
ENV_FILE = os.getenv("ENV_FILE", ".env.local")

# Load configuration - mainly for outside docker
load_dotenv(ENV_FILE)

# Logging
# TODO: Properly implement
logger = logging.getLogger(__name__)
logging.basicConfig(
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.getLevelName(LOG_LEVEL),
)


class Glucose:
    """
    Simple class to poll data from the LibreLinkUpApp
    """

    def __init__(self, email, password, auth, db_manager):
        # Initialise auth
        self.auth_manager = auth(email, password)
        self.email = email
        self.password = password
        self.db_manager = db_manager(
            os.environ["DB_USERNAME"],
            os.environ["DB_PASSWORD"],
            os.environ["DB_HOST"],
            os.environ["DB_NAME"],
        )

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
        return response.json()

    def update_cgm_data(self, patient_id):
        logger.info("update_cgm_data()")
        data = self.get_cgm_data(patient_id)
        # If no record set really far back
        last_record = self.db_manager.get_last_record()
        last_timestamp, max_id = last_record
        self.db_manager.save_glucose_data(
            self.format_cgm_data(last_timestamp, max_id, data.get("data").get("graphData"))
        )

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
        logging.debug(f"Last timestamp {last_timestamp}")
        # Filter records the new ones must be at least one second apart
        filtered_records = [
            (record.get("Value"), record.get("Timestamp"))
            for record in data
            if (
                datetime.strptime(record.get("Timestamp"), DATETIME_FORMAT) - last_timestamp
            ).total_seconds()
            > 0
        ]
        sorted_records = sorted(
            filtered_records, key=lambda x: datetime.strptime(x[1], DATETIME_FORMAT)
        )
        records_to_add = [
            (idx + max_id + 1, sorted_records[idx][0], sorted_records[idx][1])
            for idx in range(len(sorted_records))
        ]
        logging.debug(f"Adding records: {records_to_add}")
        return records_to_add


if __name__ == "__main__":
    # Dummy test for refresh
    email = os.getenv("LIBRE_EMAIL")
    password = os.getenv("LIBRE_PASSWORD")
    g = Glucose(email, password, AuthenticationManagement, PostgresManager)
    count = 0
    while count < 10:
        print(f"Iteration: {count+1}")
        patient_ids = g.get_patient_ids()
        for patient_id in patient_ids:
            g.update_cgm_data(patient_id)
        time.sleep(60 * 1)
        count += 1
