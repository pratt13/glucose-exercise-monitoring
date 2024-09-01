import logging

logger = logging.getLogger(__name__)


def libre_cron(libre):
    """Specific libre CRON as it requires a high frequency"""
    try:
        patient_ids = libre.get_patient_ids()
        for patient_id in patient_ids:
            libre.update_cgm_data(patient_id)
    except Exception as e:
        logger.error(f"Failed getting Libre data with exception\n:{e}")


def strava_cron(strava):
    """
    Specific CRON for strava as only a set number of pulls are permitted per day
    """
    try:
        strava.update_data(records_per_page=100, page=1)
    except Exception as e:
        logger.error(f"Failed getting Strava data with exception\n:{e}")


def data_cron(data):
    """
    Specific CRON for dta to mutate the fetched data
    """
    try:
        data.combine_data()
    except Exception as e:
        logger.error(
            f"Failed combining the strava data with libre ones, exception\n:{e}"
        )
