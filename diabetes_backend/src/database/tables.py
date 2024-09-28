"""
Base ORM class
"""
import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


class Base(DeclarativeBase):
    pass


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

    __time_field__ = "start_time"

    def __repr__(self) -> str:
        return f"Strava(id={self.id!r}, elapsed_time={self.elapsed_time!r}, activity_type={self.activity_type!r}, distance={self.distance!r})"


class Glucose(Base):
    __tablename__ = "glucose_level"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    glucose: Mapped[float] = mapped_column(Float)

    __time_field__ = "timestamp"

    def __repr__(self) -> str:
        return f"Glucose(id={self.id!r}, timestamp={self.timestamp!r}, glucose={self.glucose!r})"


class GlucoseExercise(Base):
    __tablename__ = "glucose_exercise"

    # TODO: Foreign key for glucose and strava

    id: Mapped[int] = mapped_column(primary_key=True)
    glucose: Mapped[float] = mapped_column(Float)
    distance: Mapped[float] = mapped_column(Float)
    activity_type: Mapped[str] = mapped_column(String)
    seconds_since_start: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    activity_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    activity_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"GlucoseExercise(id={self.id!r}, timestamp={self.timestamp!r}, activity_type={self.activity_type!r}, distance={self.distance!r})"
