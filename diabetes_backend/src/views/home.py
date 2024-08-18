import logging
from datetime import datetime as dt
from flask import request
from src.views.base import BaseView

logger = logging.getLogger("app")


class Home(BaseView):
    """
    Home App
    """

    def get(self):
        return "hello", 200
