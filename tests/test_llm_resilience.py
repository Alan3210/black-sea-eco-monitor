from types import SimpleNamespace

import pytest

from agents.news_agent.llm_resilience import (
    classify_news_with_retry,
    is_retryable_llm_error,
)


def test_retryable_oom_error_is_detected():
    error = RuntimeError(
        "CUDA error: out of memory "
        "(status code: 500)"
    )

    assert (
        is_retryable_llm_error(
            error
        )
        is True
    )


def test_retry_succeeds_after_temporary_failure():
    item = SimpleNamespace(
        title="Test"
    )

    calls = []

    expected = object()

    def fake_classifier(_item):
        calls.append(
            1
        )

        if len(calls) == 1:
            raise RuntimeError(
                "CUDA error: out of memory"
            )

        return expected

    sleep_calls = []

    result = classify_news_with_retry(
        item,
        classifier=fake_classifier,
        max_attempts=3,
        retry_delays_seconds=(
            0.25,
            0.5,
        ),
        sleep_fn=sleep_calls.append,
    )

    assert result is expected
    assert len(calls) == 2
    assert sleep_calls == [
        0.25
    ]


def test_non_retryable_error_is_not_retried():
    item = SimpleNamespace(
        title="Test"
    )

    calls = []

    def fake_classifier(_item):
        calls.append(
            1
        )

        raise ValueError(
            "Invalid structured output"
        )

    with pytest.raises(
        ValueError,
        match="Invalid structured output",
    ):
        classify_news_with_retry(
            item,
            classifier=fake_classifier,
            max_attempts=3,
            retry_delays_seconds=(
                0.0,
                0.0,
            ),
            sleep_fn=lambda _delay: None,
        )

    assert len(calls) == 1
