import requests
import time
import logging
from datetime import datetime, timedelta
from constants import BASE_URL, HEADERS

logger = logging.getLogger(__name__)


class AuthenticationManagement:
    """
    Basic Authentication Class For Libre LinkUp

    Much of this is taken from:
    https://github.com/Daniel-Elston/libre-link/tree/master
    """

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = self.login()

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def login(self, retries=3, delay=60 * 2):
        """Log in to LibreLinkUp and retrieve JWT token."""
        logger.debug("login()")
        endpoint = "/llu/auth/login"
        payload = {"email": self.email, "password": self.password}

        for attempt in range(retries + 1):
            try:
                logger.info(f"Fetching token for {self.email}")
                response = requests.post(BASE_URL + endpoint, headers=HEADERS, json=payload)
                response.raise_for_status()
                data = response.json()
                token = data.get("data", {}).get("authTicket", {}).get("token", {})
                if not token:
                    raise ValueError("Failed to get token")
                self._expiration_date = datetime.fromtimestamp(
                    data.get("data", {}).get("authTicket", {}).get("expires")
                )
                logger.debug(f"Successfully retrieved token for {self.email}")
                return token
            except requests.exceptions.HTTPError as ex:
                if ex.response.status_code == 429 and attempt < retries:
                    logger.warning(
                        f"Rate limit exceeded, waiting {delay} seconds before retrying..."
                    )
                    time.sleep(delay)
                    continue
                raise ex
            except ValueError as ex:
                logger.warning(f"Error: {ex}")
                if attempt >= retries:
                    raise ex

    def refresh_token(self, **kwargs):
        """
        Refresh token
        """
        logger.debug("refresh_token()")
        self.token = self.login(**kwargs)

    def get_token(self):
        """
        Get fresh token
        """
        logger.debug("get_token()")
        if datetime.now() >= self._expiration_date + timedelta(minutes=-2):
            self.refresh_token()
        else:
            logger.debug("Using existing token")
        return self.token
