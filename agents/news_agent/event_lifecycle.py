from dataclasses import dataclass
import re


@dataclass
class LifecycleDecision:
    status: str
    reason: str


# Order matters:
# resolved > contained > active > detected.
#
# If an article says that a fire was localized and
# firefighting continues, "contained" is the more advanced
# lifecycle state and should win over "active".
STATUS_PATTERNS = {
    "resolved": [
        # Russian: extinguished / eliminated.
        r"\bпотушен(?:а|о|ы)?\b",
        r"\bпотушил(?:а|о|и)?\b",
        r"\bликвидирован(?:а|о|ы)?\b",
        r"\bликвидировал(?:а|о|и)?\b",
        r"\bустранен(?:а|о|ы)?\b",
        r"\bустранён(?:а|о|ы)?\b",
        r"\bустранил(?:а|о|и)?\b",
        r"\bпожар\s+полностью\s+потушен\b",
        r"\bработы\s+завершен(?:ы|а|о)?\b",
        r"\bработы\s+завершён(?:ы|а|о)?\b",

        # Russian: recovery/restoration after incident.
        r"\bвосстановлен(?:а|о|ы)?\b",
        r"\bвосстановил(?:а|о|и)?\b",
        r"\bвосстановлено\s+электроснабжение\b",
        r"\bэлектроснабжение\s+восстановлен(?:о|о полностью)?\b",

        # English.
        r"\bextinguished\b",
        r"\bfully\s+extinguished\b",
        r"\bput\s+out\b",
        r"\bresolved\b",
        r"\beliminated\b",
        r"\brestored\b",
        r"\bcleanup\s+(?:was\s+)?completed\b",
        r"\bresponse\s+operations\s+completed\b",
    ],

    "contained": [
        # Russian.
        r"\bлокализован(?:а|о|ы)?\b",
        r"\bлокализировал(?:а|о|и)?\b",
        r"\bвзят(?:а|о|ы)?\s+под\s+контроль\b",
        r"\bвзял(?:а|и)?\s+под\s+контроль\b",
        r"\bраспространение\s+ограничен(?:о|а|ы)?\b",
        r"\bограничил(?:и|а|о)?\s+распространение\b",

        # English.
        r"\bcontained\b",
        r"\bbrought\s+under\s+control\b",
        r"\bunder\s+control\b",
        r"\bspread\s+has\s+been\s+limited\b",
    ],

    "active": [
        # Russian firefighting / ongoing response.
        r"\bтушат\b",
        r"\bтушение\b",
        r"\bтушении\b",
        r"\bтушить\b",
        r"\bпродолжают\s+тушить\b",
        r"\bпродолжается\s+тушение\b",
        r"\bпожар\s+продолжается\b",
        r"\bпожар\s+продолжает\b",
        r"\bпожар\s+горит\b",
        r"\bгорит\b",
        r"\bновые\s+очаги\b",
        r"\bработают\s+службы\b",
        r"\bработают\s+пожарные\b",
        r"\bзадействован(?:а|о|ы)?\s+авиаци",
        r"\bплощадь\s+(?:пожара\s+)?увеличил(?:ась|ся|ось)\b",
        r"\bплощадь\s+(?:пожара\s+)?выросл(?:а|о|и)\b",

        # Explicit future response still means the incident
        # is currently active, but it must not be "resolved".
        r"\bпланир\w*\s+(?:потушить|ликвидировать)\b",
        r"\bплан(?:ы|ах|ами)?\s+(?:потушить|ликвидировать)\b",

        # English.
        r"\b(?:plan|plans|planned|planning)\s+to\s+extinguish\b",
        r"\bbeing\s+extinguished\b",
        r"\bfirefighters\s+are\s+working\b",
        r"\bfirefighting\s+continues\b",
        r"\bcontinues\s+to\s+burn\b",
        r"\bstill\s+burning\b",
        r"\bongoing\s+fire\b",
        r"\bnew\s+hotspots\b",
        r"\baerial\s+firefighting\b",
        r"\bfire\s+area\s+(?:has\s+)?increased\b",
    ],
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("ё", "е")
    text = re.sub(
        r"[^a-zа-я0-9\s]+",
        " ",
        text,
    )
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def detect_lifecycle_status(
    title: str,
    summary: str = "",
) -> LifecycleDecision:
    text = normalize_text(
        f"{title} {summary}"
    )

    for status, patterns in STATUS_PATTERNS.items():
        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return LifecycleDecision(
                    status=status,
                    reason=(
                        "Lifecycle pattern detected: "
                        f"{match.group(0)}"
                    ),
                )

    return LifecycleDecision(
        status="detected",
        reason=(
            "No lifecycle transition marker found."
        ),
    )
