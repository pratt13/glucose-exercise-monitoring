import requests
import logging
from datetime import datetime

from src.base import Base
from src.constants import BASE_URL, DATA_TYPES, HEADERS, DATETIME_FORMAT


logger = logging.getLogger(__name__)


class Glucose(Base):
    """
    Simple class to poll data from the LibreLinkUpApp
    """

    def __init__(self, email, password, auth, db_manager):
        logger.debug(f"Glucose email: {email}")
        # Initialise auth
        self.auth_manager = auth(email, password)
        self.email = email
        self.password = password
        self.db_manager = db_manager

    @property
    def name(self):
        return "Libre"

    def get_patient_ids(self):
        """
        Retrieve patient IDs from LibreLinkUp.
        """
        logger.info("Getting patient ids for email")
        token = self.auth_manager.get_token()
        endpoint = "/llu/connections"
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.get(BASE_URL + endpoint, headers=headers)
        response.raise_for_status()
        patient_data = response.json().get("data", [])
        return [data.get("patientId") for data in patient_data]

    def get_cgm_data(self, patient_id):
        """Retrieve CGM data for a specific patient from LibreLinkUp."""
        logger.info("Getting CGM data")
        token = self.auth_manager.get_token()
        endpoint = f"/llu/connections/{patient_id}/graph"
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.get(BASE_URL + endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    def _get_last_record(self):
        """
        Get last record
        """
        logger.debug("_get_last_record()")
        return self.db_manager.get_last_record(DATA_TYPES.LIBRE)

    def get_records(self, start_time, end_time):
        """
        Get all records from the database within the given time interval
        """
        logger.debug(f"get_records({start_time}, {end_time})")
        return self.db_manager.get_records(DATA_TYPES.LIBRE, start_time, end_time)

    def _save_data(self, data):
        """
        Save date
        """
        logger.debug(f"_save_data(): {data}")
        self.db_manager.save_data(data, DATA_TYPES.LIBRE)

    def update_cgm_data(self, patient_id):
        logger.info("update_cgm_data()")
        data = self.get_cgm_data(patient_id)
        last_record = self._get_last_record()
        last_timestamp, max_id = last_record
        self._save_data(
            self.format_cgm_data(
                last_timestamp, max_id, data.get("data").get("graphData")
            )
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
        logging.debug("format_cgm_data({last_timestamp}, {max_id}, {data})")
        # Filter records the new ones must be at least one second apart
        filtered_records = [
            (record.get("Value"), record.get("Timestamp"))
            for record in data
            if (
                datetime.strptime(record.get("Timestamp"), DATETIME_FORMAT)
                - last_timestamp
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
