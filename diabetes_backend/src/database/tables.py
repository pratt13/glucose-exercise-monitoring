"""
Base ORM class
"""
import datetime
from sqlalchemy import DateTime, Float, String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, relationship, DeclarativeBase, mapped_column
from typing import List


class Base(DeclarativeBase):
    def get_as_json_object(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class Glucose(Base):
    __tablename__ = "glucose_level"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    glucose: Mapped[float] = mapped_column(Float)
    glucose_exercise: Mapped["GlucoseExercise"] = relationship(
        back_populates="glucose_rec"
    )

    __time_field__ = "timestamp"

    def __repr__(self) -> str:
        return f"Glucose(id={self.id!r}, timestamp={self.timestamp!r}, glucose={self.glucose!r})"


class Strava(Base):
    __tablename__ = "strava"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    glucose_exercise: Mapped[List["GlucoseExercise"]] = relationship(
        back_populates="strava_rec"
    )
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


class GlucoseExercise(Base):
    __tablename__ = "glucose_exercise"

    id: Mapped[int] = mapped_column(primary_key=True)
    strava_id: Mapped[int] = mapped_column(ForeignKey("strava.id"))
    strava_rec: Mapped["Strava"] = relationship(back_populates=("glucose_exercise"))
    glucose_id: Mapped[int] = mapped_column(ForeignKey("glucose_level.id"))
    glucose_rec: Mapped["Glucose"] = relationship(back_populates="glucose_exercise")

    distance: Mapped[float] = mapped_column(Float)
    activity_type: Mapped[str] = mapped_column(String)
    seconds_since_start: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    activity_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    activity_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    __time_field__ = "timestamp"

    def __repr__(self) -> str:
        return f"GlucoseExercise(id={self.id!r}, timestamp={self.timestamp!r}, activity_type={self.activity_type!r}, distance={self.distance!r}, glucose_id={self.glucose_id!r}, glucose_id={self.strava_id!r})"
