from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Base class for all Black Sea Eco Monitor agents.

    Every agent follows the same pipeline:

    collect -> analyze -> build_events
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def collect(self) -> Any:
        """
        Collect raw data from an external source.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze(self, data: Any) -> Any:
        """
        Analyze collected raw data.
        """
        raise NotImplementedError

    @abstractmethod
    def build_events(self, analysis: Any) -> list:
        """
        Convert analysis results into EnvironmentalEvent objects.
        """
        raise NotImplementedError

    def run(self) -> list:
        """
        Execute the complete agent pipeline.
        """

        raw_data = self.collect()

        analysis = self.analyze(raw_data)

        events = self.build_events(analysis)

        return events