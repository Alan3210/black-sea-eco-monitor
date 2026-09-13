import time

from agents.news_agent.llm_classifier import (
    classify_news_with_llm,
)


DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAYS_SECONDS = (
    2.0,
    5.0,
)


def is_retryable_llm_error(
    error: Exception,
) -> bool:
    message = str(error).lower()

    retryable_markers = (
        "out of memory",
        "cuda error",
        "status code: 500",
        "status code: 502",
        "status code: 503",
        "temporarily unavailable",
        "connection refused",
        "connection reset",
        "connection error",
        "timeout",
        "timed out",
    )

    return any(
        marker in message
        for marker in retryable_markers
    )


def classify_news_with_retry(
    item,
    *,
    classifier=classify_news_with_llm,
    max_attempts=DEFAULT_MAX_ATTEMPTS,
    retry_delays_seconds=(
        DEFAULT_RETRY_DELAYS_SECONDS
    ),
    sleep_fn=time.sleep,
):
    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1"
        )

    attempt = 0

    while True:
        attempt += 1

        try:
            return classifier(
                item
            )

        except Exception as error:
            should_retry = (
                attempt < max_attempts
                and is_retryable_llm_error(
                    error
                )
            )

            if not should_retry:
                raise

            delay_index = min(
                attempt - 1,
                len(
                    retry_delays_seconds
                ) - 1,
            )

            delay = (
                retry_delays_seconds[
                    delay_index
                ]
                if retry_delays_seconds
                else 0.0
            )

            print(
                "LLM RETRY"
            )

            print(
                f"  Attempt {attempt} "
                f"of {max_attempts} failed."
            )

            print(
                f"  {type(error).__name__}: "
                f"{error}"
            )

            print(
                f"  Retrying in "
                f"{delay:.1f} seconds..."
            )

            if delay > 0:
                sleep_fn(
                    delay
                )
