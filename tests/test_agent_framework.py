from agents.news_agent.agent import NewsAgent


def test_news_agent_creation():

    agent = NewsAgent()

    assert agent.name == "News Agent"


def test_news_agent_pipeline(
    monkeypatch
):

    agent = NewsAgent()


    monkeypatch.setattr(
        agent,
        "collect",
        lambda: [
            {
                "title": "Test news"
            }
        ]
    )


    monkeypatch.setattr(
        agent,
        "analyze",
        lambda data: data
    )


    monkeypatch.setattr(
        agent,
        "build_events",
        lambda analysis: []
    )


    result = agent.run()


    assert result == []