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

# SqlAlchemy
from src.glucose_new import GlucoseNew
from src.database_manager_new import DatabaseManager
from sqlalchemy import create_engine

# Configuration settings
from src.data import Data
from src.views.metric import Metric
from src.views.home import Home
from src.auth import AuthenticationManagement
from src.crons import data_cron, libre_cron, strava_cron
from src.glucose import Glucose

from src.strava import Strava
from src.utils import (
    aggregate_glucose_data,
    aggregate_strava_data,
    glucose_quartile_data,
    group_glucose_data_by_day,
    libre_data_bucketed_day_overview,
    libre_extremes_in_buckets,
    libre_hba1c,
    load_libre_credentials_from_env,
    load_strava_credentials_from_env,
    run_sum_strava_data,
)
from src.schemas import TimeIntervalSchema, TimeIntervalWithBucketSchema
from src.views.raw_data import RawData
from src.database_manager import PostgresManager

# SQL
from src.database.glucose import Base

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

# In the simplest case, initialize the Flask-Cors extension with
# default arguments in order to allow CORS for all domains on all routes.
# See the full list of options in the documentation.
# https://flask-cors.readthedocs.io/en/3.0.7/
CORS(app, origins=["http://localhost:5173"])

# Instantiate DB manager
postgres_manager = PostgresManager(
    os.environ["DB_USERNAME"],
    os.environ["DB_PASSWORD"],
    os.environ["DB_HOST"],
    os.environ["DB_NAME"],
)
# SQLAlchemy engine
# TODO - protect env vars
root = "diabetes_root:diabetes_root"
host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
url = f"postgresql+psycopg2://{root}@{host}:5432/{db_name}"
engine = create_engine(url, echo=True)


# Create if not exists
Base.metadata.create_all(engine)

# Instantiate the Glucose class
libre = Glucose(
    *load_libre_credentials_from_env(),
    AuthenticationManagement,
    postgres_manager,
)
# Instantiate the Strava class
strava = Strava(
    *load_strava_credentials_from_env(),
    postgres_manager,
)
# Instantiate the Data class
data = Data(
    postgres_manager,
)
# Instantiate the new database manager
db_manager = DatabaseManager(engine)
# Instantiate the new glucose class
glucose_new = GlucoseNew(
    *load_libre_credentials_from_env(), AuthenticationManagement, db_manager
)


# Add routing
home = Home.as_view(
    "home",
)
app.add_url_rule("/", view_func=home)
GlucoseRecords = RawData.as_view(
    "glucose",
    TimeIntervalSchema(),
    libre,
)
StravaRecords = RawData.as_view(
    "strava",
    TimeIntervalSchema(),
    strava,
)
StravaLibreRecords = RawData.as_view(
    "strava-libre",
    TimeIntervalSchema(),
    data,
)
Hba1c = Metric.as_view(
    "hba1c",
    TimeIntervalSchema(),
    libre,
    lambda x: libre_hba1c(x, 2, 1),
)
LibrePercentage = Metric.as_view(
    "libre-percentage",
    TimeIntervalSchema(),
    libre,
    lambda x: libre_extremes_in_buckets(x, 2, 1),
)
LibrePercentageDayOverview = Metric.as_view(
    "libre-percentage-day-overview",
    TimeIntervalWithBucketSchema(),
    libre,
    lambda x, **kwargs: libre_data_bucketed_day_overview(x, 2, 1, **kwargs),
)
Aggregate15min = Metric.as_view(
    "test",
    TimeIntervalSchema(),
    libre,
    lambda x, **kwargs: aggregate_glucose_data(x, 2, 1, **kwargs),
)
StravaSummary = Metric.as_view(
    "strava-summary",
    TimeIntervalSchema(),
    strava,
    lambda x: run_sum_strava_data(x, 5, 1, 2),
)
StravaLibreSummary = Metric.as_view(
    "strava-libre-summary",
    TimeIntervalSchema(),
    data,
    lambda x: glucose_quartile_data(x, 8, 3),
)
LibreQuartileSummary = Metric.as_view(
    "libre-quartile-data",
    TimeIntervalSchema(),
    libre,
    lambda x: glucose_quartile_data(x, 2, 1),
)
GroupedLibreDayData = Metric.as_view(
    "libre-grouped-day-data",
    TimeIntervalSchema(),
    libre,
    lambda x: group_glucose_data_by_day(x, 2, 1),
)
app.add_url_rule("/glucose/", view_func=GlucoseRecords)
app.add_url_rule("/strava/", view_func=StravaRecords)
app.add_url_rule("/strava-libre/", view_func=StravaLibreRecords)
app.add_url_rule("/glucose/aggregate/15min", view_func=Aggregate15min)
app.add_url_rule("/strava/summary", view_func=StravaSummary)
app.add_url_rule("/strava-libre/summary", view_func=StravaLibreSummary)
app.add_url_rule("/glucose/hba1c", view_func=Hba1c)
app.add_url_rule("/glucose/percentage", view_func=LibrePercentage)
app.add_url_rule("/glucose/percentage/day", view_func=LibrePercentageDayOverview)
app.add_url_rule("/glucose/quartile", view_func=LibreQuartileSummary)
app.add_url_rule("/glucose/days", view_func=GroupedLibreDayData)

# Move these Cron Jobs to AWS lambdas or Azure equivalents
scheduler = BackgroundScheduler()
scheduler.add_job(func=libre_cron, args=[libre], trigger="interval", seconds=300)
scheduler.add_job(func=strava_cron, args=[strava], trigger="interval", seconds=300)
scheduler.add_job(func=data_cron, args=[data], trigger="interval", seconds=300)
# New cron
scheduler.add_job(func=libre_cron, args=[glucose_new], trigger="interval", seconds=300)


with app.app_context():
    scheduler.start()


if __name__ == "__main__":

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    # Disable flask reloading the app on error, just let it die in dramatic
    # fashion. This also avoids multiple instances of any future cron jobs.
    app.run(use_reloader=False, port=int(PORT), host=HOST, threaded=True)
