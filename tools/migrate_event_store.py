import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.news_agent.event_store import EventStore


def main():
    store = EventStore()
    print(f"Migrated Event Store: {store.db_path}")
    print("Migration trigger completed successfully.")


if __name__ == "__main__":
    main()
