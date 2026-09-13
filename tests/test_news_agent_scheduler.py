import os

import pytest

from agents.news_agent.scheduler import (
    DEFAULT_INTERVAL_MINUTES,
    get_interval_minutes,
    run_scheduler,
)


def test_scheduler_default_interval(
    monkeypatch,
):
    monkeypatch.delenv(
        "NEWS_AGENT_INTERVAL_MINUTES",
        raising=False,
    )

    assert (
        get_interval_minutes()
        == DEFAULT_INTERVAL_MINUTES
    )


def test_scheduler_interval_from_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "NEWS_AGENT_INTERVAL_MINUTES",
        "15",
    )

    assert (
        get_interval_minutes()
        == 15.0
    )


def test_scheduler_runs_sequential_cycles():
    calls = []

    def fake_run_once():
        calls.append(
            "run"
        )

    def fake_sleep(seconds):
        calls.append(
            ("sleep", seconds)
        )

    run_scheduler(
        interval_minutes=30,
        run_once=fake_run_once,
        sleep_fn=fake_sleep,
        max_cycles=2,
    )

    assert calls == [
        "run",
        ("sleep", 1800.0),
        "run",
    ]


def test_scheduler_rejects_invalid_interval(
    monkeypatch,
):
    monkeypatch.setenv(
        "NEWS_AGENT_INTERVAL_MINUTES",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        get_interval_minutes()
