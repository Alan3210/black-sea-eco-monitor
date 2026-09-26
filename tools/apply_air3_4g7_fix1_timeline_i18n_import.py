from pathlib import Path

path = Path("frontend/src/evidenceTimelineRenderer.js")
text = path.read_text(encoding="utf-8")

if "from './i18n.js'" not in text and 'from "./i18n.js"' not in text:
    text = "import { t } from './i18n.js';\n\n" + text

text = text.replace(
    "export function renderEvidenceTimeline",
    "export function renderEvidenceTimeline"
)

path.write_text(text, encoding="utf-8")

print("AIR-3.4G7 fix1 evidence timeline i18n import applied")
