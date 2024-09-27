"""
Glucose Class for storing the glucose data
"""
import datetime
from sqlalchemy import DateTime, Float
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from database.base import Base


class Strava(Base):
    __tablename__ = "strava"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    glucose: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"Strava(id={self.id!r}, timestamp={self.timestamp!r}, glucose={self.glucose!r})"
