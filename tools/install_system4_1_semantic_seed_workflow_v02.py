from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "frontend" / "src" / "main.js"
I18N = REPO_ROOT / "frontend" / "src" / "i18n.js"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"marker not found: {label}")
    return text.replace(old, new, 1)


def backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"{label}.before_system4_1_{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return target


def patch_main(text: str) -> str:
    if "eventCanSeedMarineModel" in text:
        return text

    impact_import = """import {
  DEFAULT_IMPACT_THRESHOLD_KM,
  fetchDriftImpact,
  impactAssessmentsToFeatureCollection,
  impactSummaryViewModel,
} from './impact.js';
"""

    scenario_import = impact_import + """
import {
  eventCanSeedMarineModel,
  satelliteCandidateSeed,
  seedStatusKey,
} from './modelScenario.js';
"""

    text = replace_once(
        text,
        impact_import,
        scenario_import,
        "scenario imports",
    )

    state_marker = """let driftSeedSourceEventId = null;
let driftForecastSourceEventId = null;
"""

    state_replacement = state_marker + """let driftSeedSourceKind = null;
let driftSeedSourceId = null;
let driftForecastSourceKind = null;
let driftForecastSourceId = null;
"""

    text = replace_once(
        text,
        state_marker,
        state_replacement,
        "seed provenance state",
    )

    old_workflow_flags = """  const seedMatchesEvent = Boolean(
    driftSeed
    && driftSeedSourceEventId === event?.id,
  );

  const forecastMatchesEvent = Boolean(
    driftPayload
    && driftForecastSourceEventId === event?.id,
  );
"""

    new_workflow_flags = """  const eventSeedEligible = eventCanSeedMarineModel(
    event,
  );

  const seedAvailable = Boolean(driftSeed);
  const forecastAvailable = Boolean(driftPayload);
"""

    text = replace_once(
        text,
        old_workflow_flags,
        new_workflow_flags,
        "workflow flags",
    )

    old_status = """  if (driftLoading && seedMatchesEvent) {
    status.textContent = t(
      currentLanguage,
      'workflow.modelBusy',
    );
  } else if (forecastMatchesEvent) {
    status.textContent = t(
      currentLanguage,
      'workflow.forecastReady',
    );
  } else if (seedMatchesEvent) {
    status.textContent = t(
      currentLanguage,
      'workflow.prepared',
    );
  } else {
    status.textContent = t(
      currentLanguage,
      'workflow.awaiting',
    );
  }
"""

    new_status = """  if (driftLoading && seedAvailable) {
    status.textContent = t(
      currentLanguage,
      'workflow.modelBusy',
    );
  } else if (forecastAvailable) {
    status.textContent = t(
      currentLanguage,
      seedStatusKey(
        driftForecastSourceKind,
        { forecastReady: true },
      ),
    );
  } else if (seedAvailable) {
    status.textContent = t(
      currentLanguage,
      seedStatusKey(driftSeedSourceKind),
    );
  } else {
    status.textContent = t(
      currentLanguage,
      'workflow.awaiting',
    );
  }
"""

    text = replace_once(
        text,
        old_status,
        new_status,
        "workflow status",
    )

    text = replace_once(
        text,
        """  prepareButton.disabled = (
    !eventHasCoordinates
    || driftLoading
  );
""",
        """  prepareButton.disabled = (
    !eventHasCoordinates
    || !eventSeedEligible
    || driftLoading
  );
""",
        "event seed gate",
    )

    text = replace_once(
        text,
        """  screenButton.disabled = (
    !forecastMatchesEvent
    || driftLoading
    || impactLoading
  );
""",
        """  screenButton.disabled = (
    !forecastAvailable
    || driftLoading
    || impactLoading
  );
""",
        "impact screen gate",
    )

    actions_append = """  container.append(
    status,
    actions,
  );
"""

    actions_replacement = """  container.append(
    status,
    actions,
  );

  if (!eventSeedEligible) {
    container.append(
      makeElement(
        'div',
        'workflow-disclaimer',
        t(
          currentLanguage,
          'workflow.eventPointUnavailable',
        ),
      ),
    );
  }
"""

    text = replace_once(
        text,
        actions_append,
        actions_replacement,
        "event seed explanatory note",
    )

    event_prepare_marker = """function prepareDriftFromEvent(event) {
  const longitude = Number(event?.longitude);
  const latitude = Number(event?.latitude);

  if (
    !Number.isFinite(longitude)
    || !Number.isFinite(latitude)
  ) {
    return;
  }
"""

    event_prepare_replacement = """function prepareDriftFromEvent(event) {
  if (!eventCanSeedMarineModel(event)) {
    return;
  }

  const longitude = Number(event?.longitude);
  const latitude = Number(event?.latitude);

  if (
    !Number.isFinite(longitude)
    || !Number.isFinite(latitude)
  ) {
    return;
  }
"""

    text = replace_once(
        text,
        event_prepare_marker,
        event_prepare_replacement,
        "marine event gate",
    )

    text = replace_once(
        text,
        """  driftSeedSourceEventId = event.id;
  driftForecastSourceEventId = null;
  driftPayload = null;
""",
        """  driftSeedSourceEventId = event.id;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = 'event';
  driftSeedSourceId = event.id;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  driftPayload = null;
""",
        "event seed provenance",
    )

    impact_guard = """  if (
    impactLoading
    || !driftPayload
    || driftForecastSourceEventId !== event?.id
  ) {
    return;
  }
"""

    impact_guard_replacement = """  if (
    impactLoading
    || !driftPayload
  ) {
    return;
  }
"""

    text = replace_once(
        text,
        impact_guard,
        impact_guard_replacement,
        "impact scenario guard",
    )

    clear_marker = """  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  clearImpactScreening();
"""

    clear_replacement = """  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = null;
  driftSeedSourceId = null;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  clearImpactScreening();
"""

    text = replace_once(
        text,
        clear_marker,
        clear_replacement,
        "clear seed provenance",
    )

    forecast_start = """  driftLoading = true;
  driftErrorMessage = '';
  driftForecastSourceEventId = null;
  clearImpactScreening();
"""

    forecast_start_replacement = """  driftLoading = true;
  driftErrorMessage = '';
  driftForecastSourceEventId = null;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  clearImpactScreening();
"""

    text = replace_once(
        text,
        forecast_start,
        forecast_start_replacement,
        "forecast provenance reset",
    )

    forecast_success = """    driftPayload = payload;
    driftForecastSourceEventId =
      driftSeedSourceEventId;
    renderDriftMap();
"""

    forecast_success_replacement = """    driftPayload = payload;
    driftForecastSourceEventId =
      driftSeedSourceEventId;
    driftForecastSourceKind =
      driftSeedSourceKind;
    driftForecastSourceId =
      driftSeedSourceId;
    renderDriftMap();
"""

    text = replace_once(
        text,
        forecast_success,
        forecast_success_replacement,
        "forecast provenance success",
    )

    forecast_error = """    driftPayload = null;
    driftForecastSourceEventId = null;
    driftErrorMessage = error?.message || String(error);
"""

    forecast_error_replacement = """    driftPayload = null;
    driftForecastSourceEventId = null;
    driftForecastSourceKind = null;
    driftForecastSourceId = null;
    driftErrorMessage = error?.message || String(error);
"""

    text = replace_once(
        text,
        forecast_error,
        forecast_error_replacement,
        "forecast provenance error",
    )

    horizon_reset = """      driftPayload = null;
      driftForecastSourceEventId = null;
      clearImpactScreening();
"""

    horizon_reset_replacement = """      driftPayload = null;
      driftForecastSourceEventId = null;
      driftForecastSourceKind = null;
      driftForecastSourceId = null;
      clearImpactScreening();
"""

    text = replace_once(
        text,
        horizon_reset,
        horizon_reset_replacement,
        "horizon provenance reset",
    )

    manual_seed = """  driftSeed = {
    longitude: event.lngLat.lng,
    latitude: event.lngLat.lat,
  };
  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  clearImpactScreening();
"""

    manual_seed_replacement = """  driftSeed = {
    longitude: event.lngLat.lng,
    latitude: event.lngLat.lat,
  };
  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = 'manual';
  driftSeedSourceId = null;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  clearImpactScreening();
"""

    text = replace_once(
        text,
        manual_seed,
        manual_seed_replacement,
        "manual seed provenance",
    )

    sat_function_marker = """function makeSatellitePopupContent(feature) {
"""

    sat_prepare_function = """function prepareDriftFromSatelliteCandidate(
  feature,
) {
  const seed = satelliteCandidateSeed(feature);

  if (!seed) {
    return;
  }

  driftSelectionActive = false;
  driftSelectionJustConsumed = false;
  driftSeed = {
    longitude: seed.longitude,
    latitude: seed.latitude,
  };
  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = seed.sourceKind;
  driftSeedSourceId = seed.sourceId;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  driftPayload = null;
  driftErrorMessage = '';

  clearImpactScreening();

  map.getCanvas().style.cursor = '';
  renderDriftMap();
  renderDriftControls();
  refreshSelectedPanel();
}


""" + sat_function_marker

    text = replace_once(
        text,
        sat_function_marker,
        sat_prepare_function,
        "SAR seed function",
    )

    sat_disclaimer = """  root.append(
    makeElement(
      'div',
      'satellite-candidate-popup__disclaimer',
      t(currentLanguage, 'satellite.disclaimer'),
    ),
  );

  return root;
}
"""

    sat_disclaimer_replacement = """  root.append(
    makeElement(
      'div',
      'satellite-candidate-popup__disclaimer',
      t(currentLanguage, 'satellite.disclaimer'),
    ),
  );

  const candidateSeed = satelliteCandidateSeed(feature);

  if (candidateSeed) {
    const seedButton = makeWorkflowButton(
      t(currentLanguage, 'satellite.useAsSeed'),
      'workflow-button workflow-button--secondary',
    );

    seedButton.addEventListener(
      'click',
      () => {
        prepareDriftFromSatelliteCandidate(feature);

        if (satellitePopup) {
          satellitePopup.remove();
          satellitePopup = null;
        }
      },
    );

    root.append(seedButton);
  }

  return root;
}
"""

    text = replace_once(
        text,
        sat_disclaimer,
        sat_disclaimer_replacement,
        "SAR popup seed action",
    )

    return text


def patch_i18n(text: str) -> str:
    ru_marker = """    'workflow.title': 'МОДЕЛЬНЫЙ СЦЕНАРИЙ',
    'workflow.prepare': 'Использовать точку события',
    'workflow.awaiting': 'Используйте координаты события как стартовую точку модели.',
    'workflow.prepared': 'Точка события передана в OpenDrift. Настройте параметры слева и запустите прогноз.',
    'workflow.modelBusy': 'OpenDrift рассчитывает прогноз для точки события…',
    'workflow.forecastReady': 'Прогноз OpenDrift готов для этого события.',
"""

    ru_replacement = """    'workflow.title': 'МОДЕЛЬНЫЙ СЦЕНАРИЙ',
    'workflow.prepare': 'Использовать точку события',
    'workflow.awaiting': 'Выберите стартовую точку модели в море вручную, из SAR-кандидата или из подходящего морского события.',
    'workflow.eventPointUnavailable': 'Точка выбранного события недоступна как seed морской модели: разрешены только морские категории с типом локации water_body/coastal_area.',
    'workflow.preparedEvent': 'Морская точка события подготовлена для OpenDrift.',
    'workflow.preparedManual': 'Подготовлена вручную выбранная морская точка. Сценарий не привязан к подтверждённому событию.',
    'workflow.preparedSar': 'Подготовлен seed из SAR-кандидата. SAR-кандидат не является подтверждением нефтяного загрязнения.',
    'workflow.preparedUnknown': 'Стартовая точка модели подготовлена.',
    'workflow.modelBusy': 'OpenDrift рассчитывает модельный сценарий…',
    'workflow.forecastReadyEvent': 'Прогноз OpenDrift готов от морской точки события.',
    'workflow.forecastReadyManual': 'Прогноз OpenDrift готов от вручную выбранной морской точки.',
    'workflow.forecastReadySar': 'Прогноз OpenDrift готов от SAR-кандидата.',
    'workflow.forecastReadyUnknown': 'Прогноз OpenDrift готов.',
"""

    text = replace_once(
        text,
        ru_marker,
        ru_replacement,
        "RU workflow semantics",
    )

    text = text.replace(
        "'workflow.screening': 'Сопоставляем модельные частицы с известными локациями EventStore…',",
        "'workflow.screening': 'Сопоставляем модельные частицы с объектами Impact Registry…',",
        1,
    )

    text = text.replace(
        "'workflow.disclaimer': 'Это proximity screening модельного прогноза относительно известных локаций EventStore. Результат не подтверждает загрязнение, ущерб, воздействие на берег или фактическое попадание нефти.',",
        "'workflow.disclaimer': 'Это proximity screening модельного прогноза относительно объектов Impact Registry. Результат не подтверждает загрязнение, ущерб, воздействие на берег или фактическое попадание нефти.',",
        1,
    )

    sat_ru = """    'satellite.disclaimer': 'Кандидат по SAR-данным. Это не подтверждение загрязнения.',
"""
    sat_ru_repl = sat_ru + """    'satellite.useAsSeed': 'Использовать как seed OpenDrift',
"""
    text = replace_once(
        text,
        sat_ru,
        sat_ru_repl,
        "RU SAR seed label",
    )

    en_marker = """    'workflow.title': 'MODEL WORKFLOW',
    'workflow.prepare': 'Use event point',
    'workflow.awaiting': 'Use the event coordinates as the model seed.',
    'workflow.prepared': 'The event point is prepared for OpenDrift. Adjust settings on the left and run the forecast.',
    'workflow.modelBusy': 'OpenDrift is calculating a forecast from the event point…',
    'workflow.forecastReady': 'The OpenDrift forecast is ready for this event.',
"""

    en_replacement = """    'workflow.title': 'MODEL WORKFLOW',
    'workflow.prepare': 'Use event point',
    'workflow.awaiting': 'Choose a marine model seed manually, from a SAR candidate, or from an eligible marine event.',
    'workflow.eventPointUnavailable': 'The selected event point cannot seed the marine model. Only marine categories with water_body/coastal_area locations are eligible.',
    'workflow.preparedEvent': 'The marine event point is prepared for OpenDrift.',
    'workflow.preparedManual': 'A manually selected marine point is prepared. This scenario is not linked to a confirmed event.',
    'workflow.preparedSar': 'A SAR candidate seed is prepared. A SAR candidate is not confirmed oil pollution.',
    'workflow.preparedUnknown': 'The model seed is prepared.',
    'workflow.modelBusy': 'OpenDrift is calculating the model scenario…',
    'workflow.forecastReadyEvent': 'The OpenDrift forecast is ready from the marine event point.',
    'workflow.forecastReadyManual': 'The OpenDrift forecast is ready from the manually selected marine point.',
    'workflow.forecastReadySar': 'The OpenDrift forecast is ready from the SAR candidate.',
    'workflow.forecastReadyUnknown': 'The OpenDrift forecast is ready.',
"""

    text = replace_once(
        text,
        en_marker,
        en_replacement,
        "EN workflow semantics",
    )

    text = text.replace(
        "'workflow.screening': 'Comparing model particles with known EventStore locations…',",
        "'workflow.screening': 'Comparing model particles with Impact Registry objects…',",
        1,
    )

    text = text.replace(
        "'workflow.disclaimer': 'This is proximity screening of a model forecast against known EventStore locations. It does not confirm pollution, damage, shoreline impact or actual oiling.',",
        "'workflow.disclaimer': 'This is proximity screening of a model forecast against Impact Registry objects. It does not confirm pollution, damage, shoreline impact or actual oiling.',",
        1,
    )

    sat_en = """    'satellite.disclaimer': 'SAR-derived candidate only. This is not confirmed pollution.',
"""
    sat_en_repl = sat_en + """    'satellite.useAsSeed': 'Use as OpenDrift seed',
"""
    text = replace_once(
        text,
        sat_en,
        sat_en_repl,
        "EN SAR seed label",
    )

    return text


def main() -> int:
    if not MAIN.exists() or not I18N.exists():
        print("ERROR: frontend main/i18n file is missing.")
        return 2

    main_text = MAIN.read_text(encoding="utf-8")
    i18n_text = I18N.read_text(encoding="utf-8")

    if "eventCanSeedMarineModel" in main_text:
        print("SYSTEM-4.1 semantic seed workflow already installed.")
        return 0

    try:
        updated_main = patch_main(main_text)
        updated_i18n = patch_i18n(i18n_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No frontend file was modified.")
        return 3

    backups = [
        backup(MAIN, "frontend_main"),
        backup(I18N, "frontend_i18n"),
    ]

    MAIN.write_text(updated_main, encoding="utf-8")
    I18N.write_text(updated_i18n, encoding="utf-8")

    print("SYSTEM-4.1 Semantic Seed Workflow v0.2 installed.")
    print("Modified:")
    print("  frontend/src/main.js")
    print("  frontend/src/i18n.js")
    print("Added module expected from package:")
    print("  frontend/src/modelScenario.js")
    print("Semantic rules:")
    print("  land events cannot seed OpenDrift")
    print("  manual marine forecasts can be impact-screened")
    print("  SAR candidates can seed OpenDrift with explicit disclaimer")
    print("Backups:")
    for item in backups:
        print(f"  {item.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
