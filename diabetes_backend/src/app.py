""""
Simple FLASK app
"""
import os
import logging
from dotenv import load_dotenv

# Web application framework
from flask import Flask

# Cors
from flask_cors import CORS

# Cron Jobs
# Added time and atexit here as these will be removed later for Lambdas
# And a separate docker container for local cases
import atexit
from apscheduler.schedulers.background import BackgroundScheduler


# Configuration settings
from src.views.home import Home
from src.auth import AuthenticationManagement
from src.crons import libre_cron, strava_cron
from src.glucose import Glucose
from src.strava import Strava
from src.utils import load_libre_credentials_from_env, load_strava_credentials_from_env
from src.schemas import GlucoseSchema
from src.views.raw_data import RawData
from src.database_manager import PostgresManager

# Environment variables - default to non-docker patterns
ENV_FILE = os.getenv("ENV_FILE", ".env.local")

# Load environment variables
load_dotenv(ENV_FILE)


# Optional environment variables
PORT = os.getenv("PORT", "5000")
HOST = os.getenv("HOST", "localhost")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "/logs/glucose.log")

# Configure logging
logging.basicConfig(
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.getLevelName(LOG_LEVEL),
)


# Initialise Flask
app = Flask(__name__)

# In the simplest case, initialize the Flask-Cors extension with default arguments
# in order to allow CORS for all domains on all routes.
# See the full list of options in the documentation.
# https://flask-cors.readthedocs.io/en/3.0.7/
CORS(app)


libre = Glucose(
    *load_libre_credentials_from_env(),
    AuthenticationManagement,
    PostgresManager,
)
# Instantiate the Strava class
strava = Strava(
    *load_strava_credentials_from_env(),
    PostgresManager,
)


# Add routing
home = Home.as_view(
    "home",
)
app.add_url_rule("/", view_func=home)
GlucoseRecords = RawData.as_view(
    "glucose",
    GlucoseSchema(),
    libre,
)
app.add_url_rule("/glucose/", view_func=GlucoseRecords)


# Move these Cron Jobs to AWS lambdas or Azure equivalents
scheduler = BackgroundScheduler()
scheduler.add_job(func=libre_cron, args=[libre], trigger="interval", seconds=300)
scheduler.add_job(func=strava_cron, args=[strava], trigger="interval", seconds=18000)

with app.app_context():
    scheduler.start()


if __name__ == "__main__":

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    # Disable flask reloading the app on error, just let it die in dramatic fashion.
    # This also avoids multiple instances of any future cron jobs
    app.run(use_reloader=False, port=int(PORT), host=HOST, threaded=True)
