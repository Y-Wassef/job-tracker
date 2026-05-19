from abc import ABC, abstractmethod

class BaseParser(ABC):

    @abstractmethod
    def fetch_jobs(self):
        pass