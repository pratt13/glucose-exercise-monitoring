"""
Strava Class for storing the strava data
"""
import datetime
from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from database.base import Base


class Strava(Base):
    __tablename__ = "strava"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_latitude: Mapped[float] = mapped_column(Float)
    end_latitude: Mapped[float] = mapped_column(Float)
    start_longitude: Mapped[float] = mapped_column(Float)
    end_longitude: Mapped[float] = mapped_column(Float)
    distance: Mapped[float] = mapped_column(Float)
    activity_type: Mapped[str] = mapped_column(String)
    moving_time: Mapped[float] = mapped_column(Float)
    elapsed_time: Mapped[float] = mapped_column(Float)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"Strava(id={self.id!r}, elapsed_time={self.elapsed_time!r}, activity_type={self.activity_type!r}, distance={self.distance!r})"
