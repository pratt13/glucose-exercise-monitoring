from abc import ABC, abstractmethod


class Base(ABC):
    @property
    @abstractmethod
    def name(self):
        return ""

    @abstractmethod
    def get_records(self, start_time, end_time):
        pass
