from agents.base.agent import BaseAgent


class NewsAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="News Agent"
        )

    def collect(self):

        return []

    def analyze(self, data):

        return []

    def build_events(self, analysis):

        return []