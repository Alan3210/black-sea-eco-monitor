from agents.base.agent import BaseAgent
from agents.news_agent.collector import collect_rss
from agents.news_agent.filter import filter_environmental_news

from backend.config import settings


class NewsAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="News Agent"
        )

    def collect(self):

        return collect_rss(
            feed_url=settings.NEWS_RSS_URL,
            source_name=settings.NEWS_SOURCE_NAME
        )

    def analyze(self, data):

        return filter_environmental_news(data)

    def build_events(self, analysis):

        return []