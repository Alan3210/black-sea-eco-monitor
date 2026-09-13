import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_INTERVAL_MINUTES = 30.0

REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


def get_interval_minutes() -> float:
    raw_value = os.getenv(
        "NEWS_AGENT_INTERVAL_MINUTES",
        str(DEFAULT_INTERVAL_MINUTES),
    )

    try:
        interval = float(
            raw_value
        )

    except ValueError as error:
        raise ValueError(
            "NEWS_AGENT_INTERVAL_MINUTES "
            "must be a number"
        ) from error

    if interval <= 0:
        raise ValueError(
            "NEWS_AGENT_INTERVAL_MINUTES "
            "must be greater than 0"
        )

    return interval


def utc_now_string() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat(
            timespec="seconds"
        )
    )


def run_news_agent_once(
    *,
    command_runner=subprocess.run,
) -> int:
    environment = os.environ.copy()

    environment.setdefault(
        "PYTHONUTF8",
        "1",
    )

    environment.setdefault(
        "PYTHONIOENCODING",
        "utf-8",
    )

    print()
    print(
        "[NEWS SCHEDULER] "
        f"Run started at {utc_now_string()}"
    )

    result = command_runner(
        [
            sys.executable,
            "-m",
            "agents.news_agent.llm_batch",
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=False,
    )

    print(
        "[NEWS SCHEDULER] "
        f"Run finished with code "
        f"{result.returncode}"
    )

    return result.returncode


def run_scheduler(
    *,
    interval_minutes=None,
    run_once=run_news_agent_once,
    sleep_fn=time.sleep,
    max_cycles=None,
):
    if interval_minutes is None:
        interval_minutes = (
            get_interval_minutes()
        )

    if interval_minutes <= 0:
        raise ValueError(
            "interval_minutes "
            "must be greater than 0"
        )

    interval_seconds = (
        interval_minutes
        * 60.0
    )

    print(
        "[NEWS SCHEDULER] Started"
    )

    print(
        "[NEWS SCHEDULER] "
        f"Interval: "
        f"{interval_minutes:g} minutes"
    )

    print(
        "[NEWS SCHEDULER] "
        "Runs are sequential; "
        "a new run never overlaps "
        "the previous run."
    )

    cycle = 0

    try:
        while True:
            cycle += 1

            try:
                run_once()

            except Exception as error:
                print(
                    "[NEWS SCHEDULER] "
                    "Run failed:"
                )

                print(
                    "  "
                    f"{type(error).__name__}: "
                    f"{error}"
                )

            if (
                max_cycles is not None
                and cycle >= max_cycles
            ):
                return

            print(
                "[NEWS SCHEDULER] "
                f"Next run in "
                f"{interval_minutes:g} minutes."
            )

            sleep_fn(
                interval_seconds
            )

    except KeyboardInterrupt:
        print()
        print(
            "[NEWS SCHEDULER] "
            "Stopped by user."
        )


def main():
    run_scheduler()


if __name__ == "__main__":
    main()
