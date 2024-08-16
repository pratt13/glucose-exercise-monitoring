def cron(libre, strava):
    """
    CRON job that:
    * Updates Libre data
    * Updates Strava data
    """
    patient_ids = libre.get_patient_ids()
    for patient_id in patient_ids:
        libre.update_cgm_data(patient_id)
    strava.update_data(records_per_page=100, page=1)
