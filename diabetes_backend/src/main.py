import os
import time
import logging
from dotenv import load_dotenv

# Environment variables - default to non-docker patterns
ENV_FILE = os.getenv("ENV_FILE", ".env.local")

from strava import Strava
from auth import AuthenticationManagement
from database_manager import PostgresManager
from glucose import Glucose

# Load configuration - mainly for outside docker
load_dotenv(ENV_FILE)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "glucose.log")

# Logging
# TODO: Properly implement
logger = logging.getLogger(__name__)
logging.basicConfig(
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.getLevelName(LOG_LEVEL),
)


if __name__ == "__main__":
    # Libre Environment variables
    email = os.getenv("LIBRE_EMAIL")
    password = os.getenv("LIBRE_PASSWORD")
    # Strava environemnt variables
    strava_client_id = os.getenv("STRAVA_CLIENT_ID")
    strava_client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    strava_rfresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    libre = Glucose(email, password, AuthenticationManagement, PostgresManager)
    strava = Strava(strava_client_id, strava_client_secret, strava_rfresh_token, PostgresManager)
    count = 0
    while count < 10:
        logger.info(f"Iteration: {count+1}")
        patient_ids = libre.get_patient_ids()
        for patient_id in patient_ids:
            libre.update_cgm_data(patient_id)

        strava.update_data(records_per_page=100, page=1)
        time.sleep(60 * 1)
        count += 1
