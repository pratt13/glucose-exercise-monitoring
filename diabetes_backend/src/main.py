import os
import time
import logging
from dotenv import load_dotenv

# Environment variables - default to non-docker patterns
ENV_FILE = os.getenv("ENV_FILE", ".env.local")

from crons import cron
from auth import AuthenticationManagement
from database_manager import PostgresManager
from utils import (
    load_libre_credentials_from_env,
    load_strava_credentials_from_env,
)
from glucose import Glucose
from strava import Strava


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
    count = 0
    libre = Glucose(
        *load_libre_credentials_from_env(),
        AuthenticationManagement,
        PostgresManager,
    )
    strava = Strava(
        *load_strava_credentials_from_env(),
        PostgresManager,
    )
    while count < 10:
        logger.info(f"Iteration: {count+1}")
        cron(libre, strava)
        time.sleep(60 * 1)
        count += 1
