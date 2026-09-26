from pathlib import Path

path = Path("frontend/src/evidenceTimelineRenderer.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "export function renderEvidenceTimeline",
    "export function renderEvidenceTimeline"
)

# Add optional language argument to avoid breaking existing tests/callers
text = text.replace(
    "export function renderEvidenceTimeline(events = []) {",
    "export function renderEvidenceTimeline(events = [], currentLanguage = 'en') {"
)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G7 fix2 timeline language parameter applied")
