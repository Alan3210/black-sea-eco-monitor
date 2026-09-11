from agents.news_agent.agent import NewsAgent


def test_news_agent_creation():

    agent = NewsAgent()

    assert agent.name == "News Agent"


def test_news_agent_pipeline():

    agent = NewsAgent()

    result = agent.run()

    assert result == []