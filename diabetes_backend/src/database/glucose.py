"""
Glucose Class for storing the glucose data
"""
import datetime
from sqlalchemy import DateTime, Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


class Base(DeclarativeBase):
    pass


class Glucose(Base):
    __tablename__ = "glucose_level"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    glucose: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"Glucose(id={self.id!r}, timestamp={self.timestamp!r}, glucose={self.glucose!r})"
