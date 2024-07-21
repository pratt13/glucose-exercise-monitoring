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
    # g = Glucose(email, password, AuthenticationManagement, PostgresManager)
    # count = 0
    # while count < 10:
    #     print(f"Iteration: {count+1}")
    #     patient_ids = g.get_patient_ids()
    #     for patient_id in patient_ids:
    #         g.update_cgm_data(patient_id)
    #     time.sleep(60 * 1)
    #     count += 1

    # Strava
    email = os.getenv("LIBRE_EMAIL")
    password = os.getenv("LIBRE_PASSWORD")
    s = Strava(strava_client_id, strava_client_secret, strava_rfresh_token, PostgresManager)
    # logger.info(s.get_activity_data(records_per_page=200, page=1))
    logger.info(s.update_data(records_per_page=1, page=1))
