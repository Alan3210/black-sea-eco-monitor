from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND = REPO_ROOT / "frontend"
SRC = FRONTEND / "src"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "main": SRC / "main.js",
    "i18n": SRC / "i18n.js",
    "css": SRC / "style.css",
    "vite": FRONTEND / "vite.config.js",
}


def _backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"{label}.before_system4_{stamp}{path.suffix}"
    shutil.copy2(path, backup)
    return backup


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"marker not found: {label}")
    return text.replace(old, new, 1)


def patch_main(text: str) -> str:
    if "from './impact.js'" in text:
        return text

    replacements = [
        ("import {\n  fetchMonitorEventContext,\n  monitorContextViewModel,\n} from './monitorContext.js';\n", "import {\n  fetchMonitorEventContext,\n  monitorContextViewModel,\n} from './monitorContext.js';\n\nimport {\n  DEFAULT_IMPACT_THRESHOLD_KM,\n  fetchDriftImpact,\n  impactAssessmentsToFeatureCollection,\n  impactSummaryViewModel,\n} from './impact.js';\n", "SYSTEM-4 impact import"),
        ("let driftPayload = null;\nlet driftLoading = false;\nlet driftErrorMessage = '';\n", "let driftPayload = null;\nlet driftLoading = false;\nlet driftErrorMessage = '';\nlet driftSeedSourceEventId = null;\nlet driftForecastSourceEventId = null;\n\nlet impactPayload = null;\nlet impactLoading = false;\nlet impactErrorMessage = '';\nlet impactEventId = null;\nlet impactRequestToken = 0;\n\n", "SYSTEM-4 state"),
        ('function renderEventPanel(event, originGroupId = null) {\n', "function makeWorkflowButton(\n  label,\n  className = 'workflow-button',\n) {\n  const button = makeElement(\n    'button',\n    className,\n    label,\n  );\n  button.type = 'button';\n  return button;\n}\n\n\nfunction formatImpactDistance(value) {\n  const number = Number(value);\n\n  if (!Number.isFinite(number)) {\n    return null;\n  }\n\n  return number < 10\n    ? `${number.toFixed(2)} km`\n    : `${number.toFixed(1)} km`;\n}\n\n\nfunction renderModelWorkflow(container, event) {\n  container.replaceChildren();\n\n  const eventHasCoordinates = Boolean(\n    Number.isFinite(Number(event?.latitude))\n    && Number.isFinite(Number(event?.longitude)),\n  );\n\n  const seedMatchesEvent = Boolean(\n    driftSeed\n    && driftSeedSourceEventId === event?.id,\n  );\n\n  const forecastMatchesEvent = Boolean(\n    driftPayload\n    && driftForecastSourceEventId === event?.id,\n  );\n\n  const impactMatchesEvent = Boolean(\n    impactPayload\n    && impactEventId === event?.id,\n  );\n\n  const status = makeElement(\n    'div',\n    'workflow-status',\n  );\n\n  if (driftLoading && seedMatchesEvent) {\n    status.textContent = t(\n      currentLanguage,\n      'workflow.modelBusy',\n    );\n  } else if (forecastMatchesEvent) {\n    status.textContent = t(\n      currentLanguage,\n      'workflow.forecastReady',\n    );\n  } else if (seedMatchesEvent) {\n    status.textContent = t(\n      currentLanguage,\n      'workflow.prepared',\n    );\n  } else {\n    status.textContent = t(\n      currentLanguage,\n      'workflow.awaiting',\n    );\n  }\n\n  const actions = makeElement(\n    'div',\n    'workflow-actions',\n  );\n\n  const prepareButton = makeWorkflowButton(\n    t(currentLanguage, 'workflow.prepare'),\n  );\n\n  prepareButton.disabled = (\n    !eventHasCoordinates\n    || driftLoading\n  );\n\n  prepareButton.addEventListener(\n    'click',\n    () => {\n      prepareDriftFromEvent(event);\n    },\n  );\n\n  const screenButton = makeWorkflowButton(\n    t(\n      currentLanguage,\n      impactLoading\n        ? 'workflow.screeningButton'\n        : 'workflow.screen',\n      {\n        km: DEFAULT_IMPACT_THRESHOLD_KM,\n      },\n    ),\n    'workflow-button workflow-button--secondary',\n  );\n\n  screenButton.disabled = (\n    !forecastMatchesEvent\n    || driftLoading\n    || impactLoading\n  );\n\n  screenButton.addEventListener(\n    'click',\n    () => {\n      void runImpactScreening(event);\n    },\n  );\n\n  actions.append(\n    prepareButton,\n    screenButton,\n  );\n\n  container.append(\n    status,\n    actions,\n  );\n\n  if (\n    impactLoading\n    && impactEventId === event?.id\n  ) {\n    container.append(\n      makeElement(\n        'div',\n        'workflow-loading',\n        t(currentLanguage, 'workflow.screening'),\n      ),\n    );\n  } else if (\n    impactErrorMessage\n    && impactEventId === event?.id\n  ) {\n    container.append(\n      makeElement(\n        'div',\n        'workflow-error',\n        t(\n          currentLanguage,\n          'workflow.screenError',\n          { message: impactErrorMessage },\n        ),\n      ),\n    );\n  } else if (impactMatchesEvent) {\n    const vm = impactSummaryViewModel(\n      impactPayload,\n    );\n\n    const heading = makeElement(\n      'div',\n      'workflow-result-title',\n      t(currentLanguage, 'workflow.summary'),\n    );\n\n    const summaryGrid = makeElement(\n      'div',\n      'workflow-summary-grid',\n    );\n\n    summaryGrid.append(\n      makeMetric(\n        t(currentLanguage, 'workflow.targets'),\n        String(vm.targetCount),\n      ),\n      makeMetric(\n        t(currentLanguage, 'workflow.withinThreshold'),\n        String(vm.withinThresholdCount),\n      ),\n      makeMetric(\n        t(currentLanguage, 'workflow.threshold'),\n        `${vm.thresholdKm} km`,\n      ),\n    );\n\n    const list = makeElement(\n      'div',\n      'workflow-assessment-list',\n    );\n\n    for (const assessment of vm.assessments) {\n      const target = assessment?.target ?? {};\n      const card = makeElement(\n        'article',\n        'workflow-assessment',\n      );\n\n      const top = makeElement(\n        'div',\n        'workflow-assessment__top',\n      );\n\n      top.append(\n        makeElement(\n          'div',\n          'workflow-assessment__name',\n          String(\n            target.name\n            ?? t(\n              currentLanguage,\n              'workflow.unknownTarget',\n            ),\n          ),\n        ),\n      );\n\n      top.append(\n        makeElement(\n          'span',\n          assessment?.potentially_affected\n            ? 'workflow-assessment__badge workflow-assessment__badge--within'\n            : 'workflow-assessment__badge',\n          t(\n            currentLanguage,\n            assessment?.potentially_affected\n              ? 'workflow.within'\n              : 'workflow.outside',\n          ),\n        ),\n      );\n\n      const meta = [];\n\n      if (\n        assessment?.first_exposure_hours\n        !== null\n        && assessment?.first_exposure_hours\n        !== undefined\n      ) {\n        meta.push(\n          t(\n            currentLanguage,\n            'workflow.firstExposure',\n            {\n              hours:\n                assessment.first_exposure_hours,\n            },\n          ),\n        );\n      }\n\n      const distance = formatImpactDistance(\n        assessment?.minimum_distance_km,\n      );\n\n      meta.push(\n        distance\n          ? t(\n            currentLanguage,\n            'workflow.closest',\n            { distance },\n          )\n          : t(\n            currentLanguage,\n            'workflow.noDistance',\n          ),\n      );\n\n      card.append(\n        top,\n        makeElement(\n          'div',\n          'workflow-assessment__meta',\n          meta.join(' · '),\n        ),\n      );\n\n      list.append(card);\n    }\n\n    container.append(\n      heading,\n      summaryGrid,\n      list,\n    );\n  }\n\n  container.append(\n    makeElement(\n      'div',\n      'workflow-disclaimer',\n      t(currentLanguage, 'workflow.disclaimer'),\n    ),\n  );\n}\n\n\nfunction renderEventPanel(event, originGroupId = null) {\n", "workflow render helpers"),
        ('  contextSection.append(contextGrid);\n\n  eventPanelContent.append(\n    header,\n    pills,\n    metrics,\n    locationQuality,\n    timeline,\n    contextSection,\n    evidenceSection,\n  );\n', "  contextSection.append(contextGrid);\n\n  const workflowSection = makeElement(\n    'section',\n    'detail-section model-workflow',\n  );\n\n  workflowSection.append(\n    makeElement(\n      'div',\n      'detail-section__title',\n      t(currentLanguage, 'workflow.title'),\n    ),\n  );\n\n  const workflowContent = makeElement(\n    'div',\n    'workflow-content',\n  );\n\n  renderModelWorkflow(\n    workflowContent,\n    event,\n  );\n\n  workflowSection.append(\n    workflowContent,\n  );\n\n  eventPanelContent.append(\n    header,\n    pills,\n    metrics,\n    locationQuality,\n    timeline,\n    contextSection,\n    workflowSection,\n    evidenceSection,\n  );\n", "workflow event panel section"),
        ('function clearDriftForecast() {\n', "function clearImpactMapData() {\n  setGeoJSONSourceData(\n    'impact-targets',\n    emptyFeatureCollection(),\n  );\n}\n\n\nfunction clearImpactScreening() {\n  impactRequestToken += 1;\n  impactPayload = null;\n  impactLoading = false;\n  impactErrorMessage = '';\n  impactEventId = null;\n  clearImpactMapData();\n}\n\n\nfunction renderImpactMap() {\n  setGeoJSONSourceData(\n    'impact-targets',\n    impactAssessmentsToFeatureCollection(\n      impactPayload,\n    ),\n  );\n}\n\n\nfunction prepareDriftFromEvent(event) {\n  const longitude = Number(event?.longitude);\n  const latitude = Number(event?.latitude);\n\n  if (\n    !Number.isFinite(longitude)\n    || !Number.isFinite(latitude)\n  ) {\n    return;\n  }\n\n  driftSelectionActive = false;\n  driftSelectionJustConsumed = false;\n  driftSeed = {\n    longitude,\n    latitude,\n  };\n  driftSeedSourceEventId = event.id;\n  driftForecastSourceEventId = null;\n  driftPayload = null;\n  driftErrorMessage = '';\n\n  clearImpactScreening();\n\n  map.getCanvas().style.cursor = '';\n  renderDriftMap();\n  renderDriftControls();\n  refreshSelectedPanel();\n}\n\n\nasync function runImpactScreening(event) {\n  if (\n    impactLoading\n    || !driftPayload\n    || driftForecastSourceEventId !== event?.id\n  ) {\n    return;\n  }\n\n  const requestToken = ++impactRequestToken;\n\n  impactLoading = true;\n  impactErrorMessage = '';\n  impactEventId = event.id;\n\n  clearImpactMapData();\n  refreshSelectedPanel();\n\n  try {\n    const payload = await fetchDriftImpact(\n      driftPayload,\n      {\n        thresholdKm:\n          DEFAULT_IMPACT_THRESHOLD_KM,\n      },\n    );\n\n    if (requestToken !== impactRequestToken) {\n      return;\n    }\n\n    impactPayload = payload;\n    renderImpactMap();\n  } catch (error) {\n    if (requestToken !== impactRequestToken) {\n      return;\n    }\n\n    console.error(\n      '[Black Sea Eco Monitor / impact]',\n      error,\n    );\n\n    impactPayload = null;\n    impactErrorMessage =\n      error?.message || String(error);\n\n    clearImpactMapData();\n  } finally {\n    if (requestToken === impactRequestToken) {\n      impactLoading = false;\n      refreshSelectedPanel();\n    }\n  }\n}\n\n\nfunction installImpactLayer() {\n  map.addSource(\n    'impact-targets',\n    {\n      type: 'geojson',\n      data: emptyFeatureCollection(),\n    },\n  );\n\n  map.addLayer({\n    id: 'impact-targets-halo',\n    type: 'circle',\n    source: 'impact-targets',\n    paint: {\n      'circle-radius': [\n        'case',\n        ['==', ['get', 'withinThreshold'], true],\n        16,\n        11,\n      ],\n      'circle-color': [\n        'case',\n        ['==', ['get', 'withinThreshold'], true],\n        '#ffd166',\n        '#78dce8',\n      ],\n      'circle-opacity': [\n        'case',\n        ['==', ['get', 'withinThreshold'], true],\n        0.24,\n        0.11,\n      ],\n      'circle-blur': 0.45,\n    },\n  });\n\n  map.addLayer({\n    id: 'impact-targets',\n    type: 'circle',\n    source: 'impact-targets',\n    paint: {\n      'circle-radius': [\n        'case',\n        ['==', ['get', 'withinThreshold'], true],\n        7,\n        5,\n      ],\n      'circle-color': [\n        'case',\n        ['==', ['get', 'withinThreshold'], true],\n        '#ffd166',\n        '#78dce8',\n      ],\n      'circle-stroke-color': '#0a1720',\n      'circle-stroke-width': 2,\n      'circle-opacity': 0.94,\n    },\n  });\n}\n\n\nfunction clearDriftForecast() {\n", "impact runtime helpers"),
        ("function clearDriftForecast() {\n  driftSelectionActive = false;\n  driftSeed = null;\n  driftPayload = null;\n  driftLoading = false;\n  driftErrorMessage = '';\n  stopLongTask('drift');\n  map.getCanvas().style.cursor = '';\n  clearDriftMapData();\n  renderDriftControls();\n}\n", "function clearDriftForecast() {\n  driftSelectionActive = false;\n  driftSeed = null;\n  driftPayload = null;\n  driftLoading = false;\n  driftErrorMessage = '';\n  driftSeedSourceEventId = null;\n  driftForecastSourceEventId = null;\n  clearImpactScreening();\n  stopLongTask('drift');\n  map.getCanvas().style.cursor = '';\n  clearDriftMapData();\n  renderDriftControls();\n  refreshSelectedPanel();\n}\n", "drift clear linkage"),
        ("  driftLoading = true;\n  driftErrorMessage = '';\n  startLongTask('drift');\n  renderDriftControls();\n\n  try {\n", "  driftLoading = true;\n  driftErrorMessage = '';\n  driftForecastSourceEventId = null;\n  clearImpactScreening();\n  startLongTask('drift');\n  renderDriftControls();\n  refreshSelectedPanel();\n\n  try {\n", "drift run linkage start"),
        ('    driftPayload = payload;\n    renderDriftMap();\n', '    driftPayload = payload;\n    driftForecastSourceEventId =\n      driftSeedSourceEventId;\n    renderDriftMap();\n', "drift run linkage success"),
        ('    driftPayload = null;\n    driftErrorMessage = error?.message || String(error);\n', '    driftPayload = null;\n    driftForecastSourceEventId = null;\n    driftErrorMessage = error?.message || String(error);\n', "drift run linkage error"),
        ("    driftLoading = false;\n    stopLongTask('drift');\n    renderDriftControls();\n  }\n}\n", "    driftLoading = false;\n    stopLongTask('drift');\n    renderDriftControls();\n    refreshSelectedPanel();\n  }\n}\n", "drift run linkage final"),
        ('    } else if (driftPayload) {\n      driftPayload = null;\n      clearDriftMapData({ keepSeed: true });\n    }\n\n    renderDriftControls();\n', '    } else if (driftPayload) {\n      driftPayload = null;\n      driftForecastSourceEventId = null;\n      clearImpactScreening();\n      clearDriftMapData({ keepSeed: true });\n    }\n\n    renderDriftControls();\n    refreshSelectedPanel();\n', "drift horizon invalidation"),
        ('  driftSeed = {\n    longitude: event.lngLat.lng,\n    latitude: event.lngLat.lat,\n  };\n  driftSelectionActive = false;\n', '  driftSeed = {\n    longitude: event.lngLat.lng,\n    latitude: event.lngLat.lat,\n  };\n  driftSeedSourceEventId = null;\n  driftForecastSourceEventId = null;\n  clearImpactScreening();\n  driftSelectionActive = false;\n', "manual drift seed provenance"),
        ('  installCurrentLayer();\n  installDriftLayer();\n  renderCurrentsStatus();\n', '  installCurrentLayer();\n  installDriftLayer();\n  installImpactLayer();\n  renderCurrentsStatus();\n', "impact layer install"),
    ]

    for old, new, label in replacements:
        text = _replace_once(
            text,
            old,
            new,
            label,
        )

    return text


def patch_i18n(text: str) -> str:
    if "'workflow.title'" in text:
        return text

    text = _replace_once(
        text,
        "    'panel.unavailable': 'Недоступно',\n",
        "    'panel.unavailable': 'Недоступно',\n    'workflow.title': 'МОДЕЛЬНЫЙ СЦЕНАРИЙ',\n    'workflow.prepare': 'Использовать точку события',\n    'workflow.awaiting': 'Используйте координаты события как стартовую точку модели.',\n    'workflow.prepared': 'Точка события передана в OpenDrift. Настройте параметры слева и запустите прогноз.',\n    'workflow.modelBusy': 'OpenDrift рассчитывает прогноз для точки события…',\n    'workflow.forecastReady': 'Прогноз OpenDrift готов для этого события.',\n    'workflow.screen': 'Проверить объекты · {km} км',\n    'workflow.screeningButton': 'Проверка объектов…',\n    'workflow.screening': 'Сопоставляем модельные частицы с известными локациями EventStore…',\n    'workflow.screenError': 'Impact screening недоступен: {message}',\n    'workflow.summary': 'РЕЗУЛЬТАТ PROXIMITY SCREENING',\n    'workflow.targets': 'ОБЪЕКТОВ ПРОВЕРЕНО',\n    'workflow.withinThreshold': 'В ПРЕДЕЛАХ ПОРОГА',\n    'workflow.threshold': 'ПОРОГ',\n    'workflow.firstExposure': 'первое сближение +{hours} ч',\n    'workflow.closest': 'минимум {distance}',\n    'workflow.noDistance': 'нет валидной модельной дистанции',\n    'workflow.within': 'в пределах порога',\n    'workflow.outside': 'вне порога',\n    'workflow.unknownTarget': 'Неизвестная локация',\n    'workflow.disclaimer': 'Это proximity screening модельного прогноза относительно известных локаций EventStore. Результат не подтверждает загрязнение, ущерб, воздействие на берег или фактическое попадание нефти.',\n",
        "RU SYSTEM-4 translations",
    )

    return _replace_once(
        text,
        "    'panel.unavailable': 'Unavailable',\n",
        "    'panel.unavailable': 'Unavailable',\n    'workflow.title': 'MODEL WORKFLOW',\n    'workflow.prepare': 'Use event point',\n    'workflow.awaiting': 'Use the event coordinates as the model seed.',\n    'workflow.prepared': 'The event point is prepared for OpenDrift. Adjust settings on the left and run the forecast.',\n    'workflow.modelBusy': 'OpenDrift is calculating a forecast from the event point…',\n    'workflow.forecastReady': 'The OpenDrift forecast is ready for this event.',\n    'workflow.screen': 'Screen locations · {km} km',\n    'workflow.screeningButton': 'Screening locations…',\n    'workflow.screening': 'Comparing model particles with known EventStore locations…',\n    'workflow.screenError': 'Impact screening unavailable: {message}',\n    'workflow.summary': 'PROXIMITY SCREENING RESULT',\n    'workflow.targets': 'TARGETS SCREENED',\n    'workflow.withinThreshold': 'WITHIN THRESHOLD',\n    'workflow.threshold': 'THRESHOLD',\n    'workflow.firstExposure': 'first proximity +{hours} h',\n    'workflow.closest': 'minimum {distance}',\n    'workflow.noDistance': 'no valid model distance',\n    'workflow.within': 'within threshold',\n    'workflow.outside': 'outside threshold',\n    'workflow.unknownTarget': 'Unknown location',\n    'workflow.disclaimer': 'This is proximity screening of a model forecast against known EventStore locations. It does not confirm pollution, damage, shoreline impact or actual oiling.',\n",
        "EN SYSTEM-4 translations",
    )


def patch_css(text: str) -> str:
    if ".model-workflow" in text:
        return text

    return text.rstrip() + '\n\n/* ---------------------------------------------------------\n   SYSTEM-4 - Event -> OpenDrift -> Impact screening\n   --------------------------------------------------------- */\n\n.model-workflow {\n  border-top-color: rgba(255, 209, 102, 0.16);\n}\n\n.workflow-content {\n  display: grid;\n  gap: 10px;\n}\n\n.workflow-status,\n.workflow-loading,\n.workflow-error,\n.workflow-disclaimer {\n  padding: 10px 11px;\n  border: 1px solid rgba(157, 220, 236, 0.10);\n  border-radius: 9px;\n  background: rgba(255, 255, 255, 0.025);\n  color: rgba(232, 241, 247, 0.58);\n  font-size: 9px;\n  line-height: 1.5;\n}\n\n.workflow-loading {\n  border-color: rgba(255, 209, 102, 0.18);\n  color: #ffe08a;\n}\n\n.workflow-error {\n  border-color: rgba(255, 93, 93, 0.20);\n  color: #ff9595;\n}\n\n.workflow-actions {\n  display: grid;\n  grid-template-columns: 1fr 1fr;\n  gap: 7px;\n}\n\n.workflow-button {\n  min-height: 34px;\n  padding: 8px 10px;\n  border: 1px solid rgba(255, 166, 0, 0.32);\n  border-radius: 8px;\n  background: rgba(255, 138, 0, 0.10);\n  color: #ffe08a;\n  cursor: pointer;\n  font-size: 9px;\n  font-weight: 850;\n  line-height: 1.25;\n}\n\n.workflow-button--secondary {\n  border-color: rgba(115, 217, 232, 0.24);\n  background: rgba(115, 217, 232, 0.07);\n  color: #9cebf4;\n}\n\n.workflow-button:disabled {\n  opacity: 0.36;\n  cursor: not-allowed;\n}\n\n.workflow-result-title {\n  margin-top: 2px;\n  color: rgba(232, 241, 247, 0.48);\n  font-size: 8px;\n  font-weight: 950;\n  letter-spacing: 0.12em;\n}\n\n.workflow-summary-grid {\n  display: grid;\n  grid-template-columns: repeat(3, minmax(0, 1fr));\n  gap: 7px;\n}\n\n.workflow-assessment-list {\n  display: grid;\n  gap: 7px;\n}\n\n.workflow-assessment {\n  padding: 10px;\n  border: 1px solid rgba(157, 220, 236, 0.09);\n  border-radius: 9px;\n  background: rgba(255, 255, 255, 0.025);\n}\n\n.workflow-assessment__top {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: 10px;\n}\n\n.workflow-assessment__name {\n  min-width: 0;\n  color: rgba(232, 241, 247, 0.90);\n  font-size: 10px;\n  font-weight: 760;\n  overflow-wrap: anywhere;\n}\n\n.workflow-assessment__badge {\n  flex: 0 0 auto;\n  padding: 4px 7px;\n  border: 1px solid rgba(120, 220, 232, 0.18);\n  border-radius: 999px;\n  background: rgba(120, 220, 232, 0.07);\n  color: rgba(156, 235, 244, 0.82);\n  font-size: 7px;\n  font-weight: 900;\n  letter-spacing: 0.05em;\n  text-transform: uppercase;\n}\n\n.workflow-assessment__badge--within {\n  border-color: rgba(255, 209, 102, 0.28);\n  background: rgba(255, 209, 102, 0.09);\n  color: #ffe08a;\n}\n\n.workflow-assessment__meta {\n  margin-top: 7px;\n  color: rgba(232, 241, 247, 0.42);\n  font-size: 8px;\n  line-height: 1.45;\n}\n\n.workflow-disclaimer {\n  border-color: rgba(244, 201, 93, 0.14);\n  background: rgba(244, 201, 93, 0.045);\n  color: rgba(241, 224, 163, 0.66);\n}\n\n@media (max-width: 720px) {\n  .workflow-actions,\n  .workflow-summary-grid {\n    grid-template-columns: 1fr;\n  }\n}\n' + "\n"


def patch_vite(text: str) -> str:
    if "'/impact':" in text:
        return text

    return _replace_once(
        text,
        "      '/satellite': {\n        target: 'http://127.0.0.1:8000',\n        changeOrigin: false,\n      },\n",
        "      '/satellite': {\n        target: 'http://127.0.0.1:8000',\n        changeOrigin: false,\n      },\n      '/impact': {\n        target: 'http://127.0.0.1:8000',\n        changeOrigin: false,\n      },\n",
        "Vite impact proxy",
    )


def main() -> int:
    for label, path in TARGETS.items():
        if not path.exists():
            print(f"ERROR: missing target {label}: {path}")
            return 2

    originals = {
        key: path.read_text(encoding="utf-8")
        for key, path in TARGETS.items()
    }

    try:
        updated = {
            "main": patch_main(originals["main"]),
            "i18n": patch_i18n(originals["i18n"]),
            "css": patch_css(originals["css"]),
            "vite": patch_vite(originals["vite"]),
        }
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No existing frontend file was modified.")
        return 3

    changed = [
        key
        for key in TARGETS
        if updated[key] != originals[key]
    ]

    if not changed:
        print("SYSTEM-4 Event -> OpenDrift -> Impact workflow already installed.")
        return 0

    backups = []
    for key in changed:
        path = TARGETS[key]
        backups.append(
            _backup(
                path,
                f"frontend_{key}",
            )
        )

    for key in changed:
        TARGETS[key].write_text(
            updated[key],
            encoding="utf-8",
        )

    print("SYSTEM-4 Event -> OpenDrift -> Impact workflow installed.")
    print("Modified:")
    for key in changed:
        print(f"  {TARGETS[key].relative_to(REPO_ROOT)}")
    print("Added module expected from package:")
    print("  frontend/src/impact.js")
    print("Backups:")
    for backup in backups:
        print(f"  {backup.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
