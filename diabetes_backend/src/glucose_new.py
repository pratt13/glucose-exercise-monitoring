import requests
import logging
from datetime import datetime, timezone
from src.database.tables import Glucose

from src.constants import BASE_URL, HEADERS, DATETIME_FORMAT


logger = logging.getLogger(__name__)


class GlucoseNew:
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
        return self.db_manager.get_last_record(Glucose)

    def get_records_between_timestamp(self, start_time, end_time):
        """
        Get all records from the database within the given time interval
        """
        logger.debug(f"get_records({start_time}, {end_time})")
        return self.db_manager.get_records_between_timestamp(
            Glucose, start_time, end_time
        )

    def _save_data(self, data):
        """
        Save data
        """
        logger.debug(f"_save_data(): {data}")
        self.db_manager.save_data(data)

    def update_cgm_data(self, patient_id):
        logger.info("update_cgm_data()")
        data = self.get_cgm_data(patient_id)
        last_record = self._get_last_record()
        logger.debug(f"Last record: {last_record}")
        last_timestamp = last_record.timestamp
        max_id = last_record.id
        self._save_data(
            self.format_cgm_data(
                last_timestamp, max_id, data.get("data").get("graphData")
            )
        )

    @staticmethod
    def format_cgm_data(last_timestamp, max_id, data):
        """
        Format the data
        """
        logging.debug(f"format_cgm_data({last_timestamp}, {max_id}, {len(data)})")
        # Filter records the new ones must be at least one second apart
        filtered_records = [
            (record.get("Value"), record.get("Timestamp"))
            for record in data
            if (
                datetime.strptime(record.get("Timestamp"), DATETIME_FORMAT).astimezone(
                    timezone.utc
                )
                - last_timestamp
            ).total_seconds()
            > 0
        ]
        sorted_records = sorted(
            filtered_records,
            key=lambda x: datetime.strptime(x[1], DATETIME_FORMAT).astimezone(
                timezone.utc
            ),
        )
        records_to_add = [
            Glucose(
                id=idx + max_id + 1,
                timestamp=sorted_records[idx][1],
                glucose=sorted_records[idx][0],
            )
            for idx in range(len(sorted_records))
        ]
        logging.debug(f"Adding records: {records_to_add}")
        return records_to_add
