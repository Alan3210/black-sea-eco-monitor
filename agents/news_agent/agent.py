from agents.base.agent import BaseAgent

from agents.news_agent.collector import (
    collect_all_sources,
)

from agents.news_agent.filter import (
    filter_environmental_news,
)


class NewsAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="News Agent"
        )

    def collect(self):

        return collect_all_sources()

    def analyze(
        self,
        data
    ):

        return filter_environmental_news(
            data
        )

    def build_events(
        self,
        analysis
    ):

        return []