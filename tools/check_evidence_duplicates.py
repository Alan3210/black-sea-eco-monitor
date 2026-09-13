import sqlite3

db = "database/events.db"

connection = sqlite3.connect(db)

rows = connection.execute(
    """
    SELECT 
        event_id,
        url,
        COUNT(*)
    FROM event_evidence
    WHERE url IS NOT NULL
    AND length(url) > 0
    GROUP BY event_id, url
    HAVING COUNT(*) > 1
    """
).fetchall()

for row in rows:
    print(row)

print(
    "Duplicates inside same event:",
    len(rows)
)

print(rows[:20])


rows = connection.execute(
    """
    SELECT url, COUNT(DISTINCT event_id)
    FROM event_evidence
    WHERE url IS NOT NULL
    AND length(url) > 0
    GROUP BY url
    HAVING COUNT(DISTINCT event_id) > 1
    """
).fetchall()

print(
    "URLs shared by different events:",
    len(rows)
)

print(rows[:20])