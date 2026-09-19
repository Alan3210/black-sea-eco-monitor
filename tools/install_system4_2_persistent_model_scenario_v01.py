from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "frontend" / "src" / "main.js"
SCENARIO = REPO_ROOT / "frontend" / "src" / "modelScenario.js"
SCENARIO_TEST = REPO_ROOT / "frontend" / "src" / "modelScenario.test.js"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

MARKER = "SYSTEM4_2_PERSISTENT_MODEL_SCENARIO"
SCENARIO_APPEND = '\n\nexport function modelScenarioShouldPersist(\n  {\n    seedAvailable = false,\n    forecastAvailable = false,\n    driftLoading = false,\n    impactAvailable = false,\n    impactLoading = false,\n    impactError = false,\n  } = {},\n) {\n  return Boolean(\n    seedAvailable\n    || forecastAvailable\n    || driftLoading\n    || impactAvailable\n    || impactLoading\n    || impactError\n  );\n}\n'
TESTS_APPEND = "\n\ntest('persistent model scenario is hidden with no model state', () => {\n  assert.equal(modelScenarioShouldPersist(), false);\n});\n\ntest('persistent model scenario is visible for a selected seed', () => {\n  assert.equal(\n    modelScenarioShouldPersist({ seedAvailable: true }),\n    true,\n  );\n});\n\ntest('persistent model scenario is visible for a completed forecast', () => {\n  assert.equal(\n    modelScenarioShouldPersist({ forecastAvailable: true }),\n    true,\n  );\n});\n\ntest('persistent model scenario remains visible for impact state', () => {\n  assert.equal(\n    modelScenarioShouldPersist({ impactError: true }),\n    true,\n  );\n});\n"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"marker not found: {label}")
    return text.replace(old, new, 1)


def backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"{label}.before_system4_2_{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return target


def patch_scenario(text: str) -> str:
    if "modelScenarioShouldPersist" in text:
        return text
    return text.rstrip() + SCENARIO_APPEND + "\n"


def patch_scenario_test(text: str) -> str:
    if "persistent model scenario is hidden" in text:
        return text

    text = replace_once(
        text,
        """  satelliteCandidateSeed,
  seedStatusKey,
} from './modelScenario.js';
""",
        """  satelliteCandidateSeed,
  seedStatusKey,
  modelScenarioShouldPersist,
} from './modelScenario.js';
""",
        "modelScenario test import",
    )
    return text.rstrip() + TESTS_APPEND + "\n"


def patch_main(text: str) -> str:
    if MARKER in text:
        return text

    text = replace_once(
        text,
        """import {
  eventCanSeedMarineModel,
  satelliteCandidateSeed,
  seedStatusKey,
} from './modelScenario.js';
""",
        """import {
  eventCanSeedMarineModel,
  satelliteCandidateSeed,
  seedStatusKey,
  modelScenarioShouldPersist,
} from './modelScenario.js';
""",
        "model scenario helper import",
    )

    text = replace_once(
        text,
        """function refreshSelectedPanel() {
  if (selectedEventId && selectedEventIsVisible()) {
    const event = eventsById.get(selectedEventId);

    if (event) {
      renderEventPanel(
        event,
        selectedGroupId,
      );
    }

    return;
  }

  if (selectedGroupId) {
    const group = getVisibleGroup(selectedGroupId);

    if (group?.isGroup) {
      renderGroupPanel(group);
    }
  }
}
""",
        """// SYSTEM4_2_PERSISTENT_MODEL_SCENARIO
function modelScenarioActive() {
  return modelScenarioShouldPersist({
    seedAvailable: Boolean(driftSeed),
    forecastAvailable: Boolean(driftPayload),
    driftLoading,
    impactAvailable: Boolean(impactPayload),
    impactLoading,
    impactError: Boolean(impactErrorMessage),
  });
}

function renderStandaloneModelScenarioPanel() {
  panelRenderToken += 1;
  eventPanelContent.replaceChildren();

  const workflowSection = makeElement(
    'section',
    'detail-section model-workflow',
  );

  workflowSection.append(
    makeElement(
      'div',
      'detail-section__title',
      t(currentLanguage, 'workflow.title'),
    ),
  );

  const workflowContent = makeElement(
    'div',
    'workflow-content',
  );

  renderModelWorkflow(workflowContent, null);
  workflowSection.append(workflowContent);
  eventPanelContent.append(workflowSection);

  eventPanel.classList.add('event-panel--open');
  eventPanel.setAttribute('aria-hidden', 'false');
}

function closeEventPanelIfIdle() {
  if (
    selectedEventId
    || selectedGroupId
    || modelScenarioActive()
  ) {
    return;
  }

  eventPanel.classList.remove('event-panel--open');
  eventPanel.setAttribute('aria-hidden', 'true');
}

function refreshSelectedPanel() {
  if (selectedEventId && selectedEventIsVisible()) {
    const event = eventsById.get(selectedEventId);

    if (event) {
      renderEventPanel(
        event,
        selectedGroupId,
      );
    }
    return;
  }

  if (selectedGroupId) {
    const group = getVisibleGroup(selectedGroupId);

    if (group?.isGroup) {
      renderGroupPanel(group);
      return;
    }
  }

  if (modelScenarioActive()) {
    renderStandaloneModelScenarioPanel();
    return;
  }

  closeEventPanelIfIdle();
}
""",
        "persistent panel refresh",
    )

    text = replace_once(
        text,
        """  const impactMatchesEvent = Boolean(
    impactPayload
    && impactEventId === event?.id,
  );
""",
        """  const impactMatchesScenario = Boolean(
    impactPayload,
  );
""",
        "impact scenario match",
    )

    text = replace_once(
        text,
        """  actions.append(
    prepareButton,
    screenButton,
  );
""",
        """  if (event) {
    actions.append(prepareButton);
  }

  actions.append(screenButton);
""",
        "standalone workflow actions",
    )

    text = replace_once(
        text,
        """  if (!eventSeedEligible) {
""",
        """  if (event && !eventSeedEligible) {
""",
        "event-only seed warning",
    )

    text = replace_once(
        text,
        """  if (
    impactLoading
    && impactEventId === event?.id
  ) {
""",
        """  if (impactLoading) {
""",
        "impact loading is scenario scoped",
    )

    text = replace_once(
        text,
        """  } else if (
    impactErrorMessage
    && impactEventId === event?.id
  ) {
""",
        """  } else if (impactErrorMessage) {
""",
        "impact error is scenario scoped",
    )

    text = replace_once(
        text,
        """  } else if (impactMatchesEvent) {
""",
        """  } else if (impactMatchesScenario) {
""",
        "impact result is scenario scoped",
    )

    text = replace_once(
        text,
        """  updateSelectedCircle();
  updateSelectedGroupMarker();

  eventPanel.classList.remove(
    'event-panel--open',
  );

  eventPanel.setAttribute(
    'aria-hidden',
    'true',
  );
}
""",
        """  updateSelectedCircle();
  updateSelectedGroupMarker();

  if (modelScenarioActive()) {
    renderStandaloneModelScenarioPanel();
    return;
  }

  eventPanel.classList.remove(
    'event-panel--open',
  );

  eventPanel.setAttribute(
    'aria-hidden',
    'true',
  );
}
""",
        "preserve scenario when event closes",
    )

    text = replace_once(
        text,
        """async function runImpactScreening(event) {
""",
        """async function runImpactScreening(event = null) {
""",
        "optional event for impact screening",
    )

    text = replace_once(
        text,
        """  impactEventId = event.id;
""",
        """  impactEventId = event?.id ?? null;
""",
        "optional impact event id",
    )

    text = replace_once(
        text,
        """  renderDriftMap();
  renderDriftControls();
});


map.on('load', () => {
""",
        """  renderDriftMap();
  renderDriftControls();
  refreshSelectedPanel();
});


map.on('load', () => {
""",
        "manual seed opens scenario panel",
    )

    return text


def main() -> int:
    for path in [MAIN, SCENARIO, SCENARIO_TEST]:
        if not path.exists():
            print(f"ERROR: required file missing: {path}")
            return 2

    main_text = MAIN.read_text(encoding="utf-8")
    scenario_text = SCENARIO.read_text(encoding="utf-8")
    test_text = SCENARIO_TEST.read_text(encoding="utf-8")

    if MARKER in main_text:
        print("SYSTEM-4.2 persistent model scenario already installed.")
        return 0

    try:
        updated_main = patch_main(main_text)
        updated_scenario = patch_scenario(scenario_text)
        updated_test = patch_scenario_test(test_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No frontend file was modified.")
        return 3

    backups = [
        backup(MAIN, "frontend_main"),
        backup(SCENARIO, "modelScenario"),
        backup(SCENARIO_TEST, "modelScenario_test"),
    ]

    MAIN.write_text(updated_main, encoding="utf-8")
    SCENARIO.write_text(updated_scenario, encoding="utf-8")
    SCENARIO_TEST.write_text(updated_test, encoding="utf-8")

    print("SYSTEM-4.2 Persistent Model Scenario v0.1 installed.")
    print("Modified:")
    print("  frontend/src/main.js")
    print("  frontend/src/modelScenario.js")
    print("  frontend/src/modelScenario.test.js")
    print("Behavior:")
    print("  manual/SAR scenario persists without a selected Event")
    print("  completed manual forecast can run Impact Screening")
    print("  closing an Event falls back to the active Model Scenario")
    print("  Impact state is scenario-scoped, not Event-scoped")
    print("Backups:")
    for item in backups:
        print(f"  {item.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
