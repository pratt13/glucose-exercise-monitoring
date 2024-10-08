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
from sqlalchemy import create_engine


from src.data import DataManager
from src.strava import StravaManager
from src.glucose import GlucoseManager
from src.database_manager import DatabaseManager

# Configuration settings
from src.views.metric import Metric
from src.views.home import Home
from src.auth import AuthenticationManagement
from src.crons import data_cron, libre_cron, strava_cron

from src.utils import (
    aggregate_glucose_data,
    glucose_quartile_data,
    glucose_raw_data,
    group_glucose_data_by_day,
    libre_data_bucketed_day_overview,
    libre_extremes_in_buckets,
    libre_hba1c,
    load_libre_credentials_from_env,
    load_strava_credentials_from_env,
    run_sum_strava_data,
    strava_glucose_raw_data,
    strava_raw_data,
)
from src.schemas import TimeIntervalSchema, TimeIntervalWithBucketSchema

# SQL
from src.database.tables import Base

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

# SQLAlchemy engine
# TODO - protect env vars
root = "diabetes_root:diabetes_root"
host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
url = f"postgresql+psycopg2://{root}@{host}:5432/{db_name}"
engine = create_engine(url, echo=True)


# Create if not exists
Base.metadata.create_all(engine)


# Instantiate the new database manager
db_manager = DatabaseManager(engine)
# Instantiate the Strava class
strava = StravaManager(*load_strava_credentials_from_env(), db_manager)
# Instantiate the new glucose class
glucose_manager = GlucoseManager(
    *load_libre_credentials_from_env(), AuthenticationManagement, db_manager
)
# Instantiate the Data class
data_manager = DataManager(db_manager)

# Add routing
home = Home.as_view(
    "home",
)
app.add_url_rule("/", view_func=home)
GlucoseRecords = Metric.as_view(
    "glucose",
    TimeIntervalSchema(),
    glucose_manager,
    lambda x: glucose_raw_data(x),
)
StravaRecords = Metric.as_view(
    "strava",
    TimeIntervalSchema(),
    strava,
    lambda x: strava_raw_data(x),
)
StravaLibreRecords = Metric.as_view(
    "strava-libre",
    TimeIntervalSchema(),
    data_manager,
    lambda x: strava_glucose_raw_data(x),
)
Hba1c = Metric.as_view(
    "hba1c",
    TimeIntervalSchema(),
    glucose_manager,
    lambda x: libre_hba1c(x),
)
LibrePercentage = Metric.as_view(
    "libre-percentage",
    TimeIntervalSchema(),
    glucose_manager,
    lambda x: libre_extremes_in_buckets(x),
)
LibrePercentageDayOverview = Metric.as_view(
    "libre-percentage-day-overview",
    TimeIntervalWithBucketSchema(),
    glucose_manager,
    lambda x, **kwargs: libre_data_bucketed_day_overview(x, **kwargs),
)
Aggregate15min = Metric.as_view(
    "test",
    TimeIntervalSchema(),
    glucose_manager,
    lambda x, **kwargs: aggregate_glucose_data(x, **kwargs),
)
StravaSummary = Metric.as_view(
    "strava-summary",
    TimeIntervalSchema(),
    strava,
    lambda x: run_sum_strava_data(x),
)
StravaLibreSummary = Metric.as_view(
    "strava-libre-summary",
    TimeIntervalSchema(),
    data_manager,
    lambda x: glucose_quartile_data(x),
)
LibreQuartileSummary = Metric.as_view(
    "libre-quartile-data",
    TimeIntervalSchema(),
    glucose_manager,
    lambda x: glucose_quartile_data(x),
)
GroupedLibreDayData = Metric.as_view(
    "libre-grouped-day-data",
    TimeIntervalSchema(),
    glucose_manager,
    lambda x: group_glucose_data_by_day(x),
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
# TO disable
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=libre_cron, args=[glucose_manager], trigger="interval", seconds=300
)
scheduler.add_job(func=strava_cron, args=[strava], trigger="interval", seconds=300)
scheduler.add_job(func=data_cron, args=[data_manager], trigger="interval", seconds=30)


with app.app_context():
    scheduler.start()

if __name__ == "__main__":

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    # Disable flask reloading the app on error, just let it die in dramatic
    # fashion. This also avoids multiple instances of any future cron jobs.
    app.run(use_reloader=False, port=int(PORT), host=HOST, threaded=True)
