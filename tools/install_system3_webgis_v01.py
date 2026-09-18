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
    "index": FRONTEND / "index.html",
    "i18n": SRC / "i18n.js",
    "css": SRC / "style.css",
    "vite": FRONTEND / "vite.config.js",
}

def _backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"{label}.before_system3_{stamp}{path.suffix}"
    shutil.copy2(path, backup)
    return backup

def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"marker not found: {label}")
    return text.replace(old, new, 1)

def patch_main(text: str) -> str:
    if "fetchSatelliteCandidates" in text:
        return text
    replacements = [
        ("import {\n  longTaskViewModel,\n} from './longTask.js';\n", "import {\n  longTaskViewModel,\n} from './longTask.js';\n\nimport {\n  fetchSatelliteCandidates,\n  satelliteCandidateViewModel,\n} from './satellite.js';\n\nimport {\n  fetchMonitorEventContext,\n  monitorContextViewModel,\n} from './monitorContext.js';\n", "SYSTEM-3 imports"),
        ("const eventPanel = document.getElementById('event-panel');\n", "const satelliteToggle = document.getElementById(\n  'satellite-layer-toggle',\n);\nconst satelliteNote = document.getElementById(\n  'satellite-layer-note',\n);\n\nconst eventPanel = document.getElementById('event-panel');\n", "satellite DOM refs"),
        ('const evidenceRequests = new Map();\n', 'const evidenceRequests = new Map();\nconst contextCache = new Map();\nconst contextRequests = new Map();\n', "context caches"),
        ("let driftErrorMessage = '';\n", "let driftErrorMessage = '';\nlet satelliteCandidatesPayload = null;\nlet satelliteCandidatesLoading = false;\nlet satelliteCandidatesErrorMessage = '';\nlet satellitePopup = null;\n", "satellite state"),
        ('function renderEventPanel(event, originGroupId = null) {\n', "function loadContext(eventId) {\n  if (contextCache.has(eventId)) {\n    return Promise.resolve(\n      contextCache.get(eventId),\n    );\n  }\n\n  if (contextRequests.has(eventId)) {\n    return contextRequests.get(eventId);\n  }\n\n  const request = fetchMonitorEventContext(eventId)\n    .then((context) => {\n      contextCache.set(eventId, context);\n      return context;\n    })\n    .finally(() => {\n      contextRequests.delete(eventId);\n    });\n\n  contextRequests.set(eventId, request);\n  return request;\n}\n\nfunction renderContextGrid(container, context) {\n  container.replaceChildren();\n\n  const vm = monitorContextViewModel(context);\n  const yesNo = (value) => t(\n    currentLanguage,\n    value ? 'panel.ready' : 'panel.unavailable',\n  );\n\n  container.append(\n    makeMetric(\n      t(currentLanguage, 'panel.satelliteObservations'),\n      String(vm.satelliteCount),\n    ),\n    makeMetric(\n      t(currentLanguage, 'panel.driftReady'),\n      yesNo(vm.driftReady),\n    ),\n    makeMetric(\n      t(currentLanguage, 'panel.impactReady'),\n      yesNo(vm.impactReady),\n    ),\n    makeMetric(\n      t(currentLanguage, 'panel.arReady'),\n      yesNo(vm.arReady),\n    ),\n  );\n}\n\nfunction renderEventPanel(event, originGroupId = null) {\n", "context helpers"),
        ('  eventPanelContent.append(\n    header,\n    pills,\n    metrics,\n    locationQuality,\n    timeline,\n    evidenceSection,\n  );\n', "  const contextSection = makeElement(\n    'section',\n    'detail-section',\n  );\n\n  contextSection.append(\n    makeElement(\n      'div',\n      'detail-section__title',\n      t(currentLanguage, 'panel.systemContext'),\n    ),\n  );\n\n  const contextGrid = makeElement(\n    'div',\n    'detail-context-grid',\n  );\n\n  contextGrid.append(\n    makeElement(\n      'div',\n      'evidence-loading detail-context-status',\n      t(currentLanguage, 'panel.contextLoading'),\n    ),\n  );\n\n  contextSection.append(contextGrid);\n\n  eventPanelContent.append(\n    header,\n    pills,\n    metrics,\n    locationQuality,\n    timeline,\n    contextSection,\n    evidenceSection,\n  );\n", "event context section"),
        ('  loadEvidence(event.id)\n', "  loadContext(event.id)\n    .then((context) => {\n      if (\n        token !== panelRenderToken\n        || selectedEventId !== event.id\n      ) {\n        return;\n      }\n\n      renderContextGrid(\n        contextGrid,\n        context,\n      );\n    })\n    .catch((error) => {\n      if (\n        token !== panelRenderToken\n        || selectedEventId !== event.id\n      ) {\n        return;\n      }\n\n      contextGrid.replaceChildren(\n        makeElement(\n          'div',\n          'evidence-error detail-context-status',\n          t(\n            currentLanguage,\n            'panel.contextUnavailable',\n            { message: error.message },\n          ),\n        ),\n      );\n    });\n\n  loadEvidence(event.id)\n", "context fetch"),
        ('function localizeStaticDom() {\n', "function satelliteLayerVisible() {\n  return Boolean(satelliteToggle?.checked);\n}\n\nfunction setSatelliteLayerVisibility(visible) {\n  const visibility = visible\n    ? 'visible'\n    : 'none';\n\n  for (const layerId of [\n    'satellite-candidates-fill',\n    'satellite-candidates-line',\n  ]) {\n    if (map.getLayer(layerId)) {\n      map.setLayoutProperty(\n        layerId,\n        'visibility',\n        visibility,\n      );\n    }\n  }\n\n  if (!visible && satellitePopup) {\n    satellitePopup.remove();\n    satellitePopup = null;\n  }\n}\n\nfunction renderSatelliteStatus() {\n  if (!satelliteNote) return;\n\n  satelliteNote.classList.toggle(\n    'satellite-layer-note--loading',\n    satelliteCandidatesLoading,\n  );\n  satelliteNote.classList.toggle(\n    'satellite-layer-note--error',\n    Boolean(satelliteCandidatesErrorMessage),\n  );\n\n  if (!satelliteLayerVisible()) {\n    satelliteNote.textContent = t(\n      currentLanguage,\n      'satellite.off',\n    );\n    return;\n  }\n\n  if (satelliteCandidatesLoading) {\n    satelliteNote.textContent = t(\n      currentLanguage,\n      'satellite.loading',\n    );\n    return;\n  }\n\n  if (satelliteCandidatesErrorMessage) {\n    satelliteNote.textContent = t(\n      currentLanguage,\n      'satellite.error',\n      {\n        message: satelliteCandidatesErrorMessage,\n      },\n    );\n    return;\n  }\n\n  satelliteNote.textContent = t(\n    currentLanguage,\n    'satellite.ready',\n    {\n      count: satelliteCandidatesPayload?.features?.length ?? 0,\n    },\n  );\n}\n\nfunction makeSatellitePopupContent(feature) {\n  const vm = satelliteCandidateViewModel(feature);\n  const root = makeElement(\n    'div',\n    'satellite-candidate-popup',\n  );\n\n  root.append(\n    makeElement(\n      'div',\n      'satellite-candidate-popup__title',\n      t(currentLanguage, 'satellite.popupTitle'),\n    ),\n  );\n\n  const rows = [\n    [\n      t(currentLanguage, 'satellite.area'),\n      vm.areaKm2 == null\n        ? '—'\n        : `${vm.areaKm2.toFixed(5)} km²`,\n    ],\n    [\n      t(currentLanguage, 'satellite.meanVv'),\n      vm.meanVvDb == null\n        ? '—'\n        : `${vm.meanVvDb.toFixed(2)} dB`,\n    ],\n    [\n      t(currentLanguage, 'satellite.threshold'),\n      vm.thresholdDb == null\n        ? '—'\n        : `${vm.thresholdDb.toFixed(1)} dB`,\n    ],\n    [\n      t(currentLanguage, 'satellite.reviewStatus'),\n      vm.reviewStatus,\n    ],\n  ];\n\n  for (const [label, value] of rows) {\n    const row = makeElement(\n      'div',\n      'satellite-candidate-popup__row',\n    );\n    row.append(\n      makeElement(\n        'div',\n        'satellite-candidate-popup__key',\n        label,\n      ),\n      makeElement(\n        'div',\n        'satellite-candidate-popup__value',\n        value,\n      ),\n    );\n    root.append(row);\n  }\n\n  root.append(\n    makeElement(\n      'div',\n      'satellite-candidate-popup__disclaimer',\n      t(currentLanguage, 'satellite.disclaimer'),\n    ),\n  );\n\n  return root;\n}\n\nfunction installSatelliteLayer() {\n  map.addSource(\n    'satellite-candidates',\n    {\n      type: 'geojson',\n      data: emptyFeatureCollection(),\n    },\n  );\n\n  map.addLayer({\n    id: 'satellite-candidates-fill',\n    type: 'fill',\n    source: 'satellite-candidates',\n    layout: {\n      visibility: 'none',\n    },\n    paint: {\n      'fill-color': '#c77dff',\n      'fill-opacity': 0.22,\n    },\n  });\n\n  map.addLayer({\n    id: 'satellite-candidates-line',\n    type: 'line',\n    source: 'satellite-candidates',\n    layout: {\n      visibility: 'none',\n    },\n    paint: {\n      'line-color': '#e0aaff',\n      'line-width': 2.2,\n      'line-opacity': 0.95,\n    },\n  });\n\n  map.on(\n    'mouseenter',\n    'satellite-candidates-fill',\n    () => {\n      map.getCanvas().style.cursor = 'pointer';\n    },\n  );\n\n  map.on(\n    'mouseleave',\n    'satellite-candidates-fill',\n    () => {\n      map.getCanvas().style.cursor = '';\n    },\n  );\n\n  map.on(\n    'click',\n    'satellite-candidates-fill',\n    (event) => {\n      if (\n        driftSelectionActive\n        || driftSelectionJustConsumed\n      ) return;\n\n      const feature = event.features?.[0];\n\n      if (!feature) return;\n\n      if (satellitePopup) {\n        satellitePopup.remove();\n      }\n\n      satellitePopup = new maplibregl.Popup({\n        closeButton: true,\n        closeOnClick: true,\n        offset: 10,\n      })\n        .setLngLat(event.lngLat)\n        .setDOMContent(\n          makeSatellitePopupContent(feature),\n        )\n        .addTo(map);\n    },\n  );\n}\n\nasync function refreshSatelliteCandidates() {\n  if (\n    !satelliteLayerVisible()\n    || satelliteCandidatesLoading\n  ) {\n    return;\n  }\n\n  satelliteCandidatesLoading = true;\n  satelliteCandidatesErrorMessage = '';\n  renderSatelliteStatus();\n\n  try {\n    const payload = await fetchSatelliteCandidates();\n\n    satelliteCandidatesPayload = payload;\n\n    setGeoJSONSourceData(\n      'satellite-candidates',\n      payload,\n    );\n\n    setSatelliteLayerVisibility(true);\n  } catch (error) {\n    console.error(\n      '[Black Sea Eco Monitor / satellite]',\n      error,\n    );\n    satelliteCandidatesErrorMessage =\n      error?.message || String(error);\n\n    if (!satelliteCandidatesPayload) {\n      setSatelliteLayerVisibility(false);\n    }\n  } finally {\n    satelliteCandidatesLoading = false;\n    renderSatelliteStatus();\n  }\n}\n\nsatelliteToggle?.addEventListener(\n  'change',\n  () => {\n    if (satelliteLayerVisible()) {\n      setSatelliteLayerVisibility(true);\n      void refreshSatelliteCandidates();\n    } else {\n      setSatelliteLayerVisibility(false);\n      renderSatelliteStatus();\n    }\n  },\n);\n\nfunction localizeStaticDom() {\n", "satellite map functions"),
        ('  renderDriftControls();\n\n  if (currentsPopup) {\n', '  renderDriftControls();\n  renderSatelliteStatus();\n\n  if (currentsPopup) {\n', "language satellite refresh"),
        ("map.on('load', () => {\n  installRegionalFocus(map);\n  installEventLayer();\n", "map.on('load', () => {\n  installRegionalFocus(map);\n  installSatelliteLayer();\n  installEventLayer();\n", "satellite layer install order"),
        ('  renderDriftControls();\n\n  void refreshEvents();\n', '  renderDriftControls();\n  renderSatelliteStatus();\n\n  void refreshEvents();\n', "satellite initial status"),
    ]
    for old, new, label in replacements:
        text = _replace_once(text, old, new, label)
    return text

def patch_index(text: str) -> str:
    if 'id="satellite-layer-toggle"' in text:
        return text
    return _replace_once(
        text,
        '          <div class="filter-section">\n            <div class="filter-section__title" data-i18n="filters.timeWindow">ПЕРИОД</div>\n',
        '          <div class="filter-section">\n            <div class="filter-section__title" data-i18n="satellite.layers">\n              СПУТНИК\n            </div>\n\n            <label class="filter-check filter-check--layer">\n              <input\n                id="satellite-layer-toggle"\n                type="checkbox"\n              />\n              <span class="satellite-layer-symbol" aria-hidden="true">SAR</span>\n              <span data-i18n="satellite.candidates">\n                SAR-кандидаты\n              </span>\n            </label>\n\n            <div\n              id="satellite-layer-note"\n              class="filter-note satellite-layer-note"\n              aria-live="polite"\n              data-i18n="satellite.off"\n            >\n              Sentinel-1 · производные кандидаты\n            </div>\n          </div>\n\n          <div class="filter-section">\n            <div class="filter-section__title" data-i18n="filters.timeWindow">ПЕРИОД</div>\n',
        "satellite filter section",
    )

def patch_i18n(text: str) -> str:
    if "'satellite.layers'" in text:
        return text
    text = _replace_once(
        text,
        "    'ocean.source': 'ИСТОЧНИК',\n",
        "    'ocean.source': 'ИСТОЧНИК',\n    'satellite.layers': 'СПУТНИК',\n    'satellite.candidates': 'SAR-кандидаты',\n    'satellite.off': 'Sentinel-1 · производные кандидаты',\n    'satellite.loading': 'Загрузка SAR-кандидатов…',\n    'satellite.ready': 'Sentinel-1 · {count} кандидатов',\n    'satellite.error': 'SAR-кандидаты недоступны: {message}',\n    'satellite.popupTitle': 'SAR DARK-SPOT CANDIDATE',\n    'satellite.area': 'ПЛОЩАДЬ',\n    'satellite.meanVv': 'СРЕДНИЙ VV',\n    'satellite.threshold': 'ПОРОГ',\n    'satellite.reviewStatus': 'СТАТУС ПРОВЕРКИ',\n    'satellite.disclaimer': 'Кандидат по SAR-данным. Это не подтверждение загрязнения.',\n    'panel.systemContext': 'СИСТЕМНЫЙ КОНТЕКСТ',\n    'panel.contextLoading': 'Загрузка системного контекста…',\n    'panel.contextUnavailable': 'Контекст недоступен: {message}',\n    'panel.satelliteObservations': 'СПУТНИКОВЫЕ НАБЛЮДЕНИЯ',\n    'panel.driftReady': 'OPENDrift',\n    'panel.impactReady': 'IMPACT SCREENING',\n    'panel.arReady': 'AR-СЦЕНА',\n    'panel.ready': 'Доступно',\n    'panel.unavailable': 'Недоступно',\n",
        "RU SYSTEM-3 translations",
    )
    return _replace_once(
        text,
        "    'ocean.source': 'SOURCE',\n",
        "    'ocean.source': 'SOURCE',\n    'satellite.layers': 'SATELLITE',\n    'satellite.candidates': 'SAR candidates',\n    'satellite.off': 'Sentinel-1 · derived candidates',\n    'satellite.loading': 'Loading SAR candidates…',\n    'satellite.ready': 'Sentinel-1 · {count} candidates',\n    'satellite.error': 'SAR candidates unavailable: {message}',\n    'satellite.popupTitle': 'SAR DARK-SPOT CANDIDATE',\n    'satellite.area': 'AREA',\n    'satellite.meanVv': 'MEAN VV',\n    'satellite.threshold': 'THRESHOLD',\n    'satellite.reviewStatus': 'REVIEW STATUS',\n    'satellite.disclaimer': 'SAR-derived candidate only. This is not confirmed pollution.',\n    'panel.systemContext': 'SYSTEM CONTEXT',\n    'panel.contextLoading': 'Loading system context…',\n    'panel.contextUnavailable': 'Context unavailable: {message}',\n    'panel.satelliteObservations': 'SATELLITE OBSERVATIONS',\n    'panel.driftReady': 'OPENDrift',\n    'panel.impactReady': 'IMPACT SCREENING',\n    'panel.arReady': 'AR SCENE',\n    'panel.ready': 'Available',\n    'panel.unavailable': 'Unavailable',\n",
        "EN SYSTEM-3 translations",
    )

def patch_css(text: str) -> str:
    if ".satellite-layer-symbol" in text:
        return text
    return text.rstrip() + '\n\n/* ---------------------------------------------------------\n   SYSTEM-3 - Satellite candidates + unified context\n   --------------------------------------------------------- */\n\n.satellite-layer-symbol {\n  min-width: 30px;\n  height: 18px;\n  display: inline-grid;\n  place-items: center;\n  flex: 0 0 auto;\n  border: 1px solid rgba(207, 122, 255, 0.34);\n  border-radius: 6px;\n  background: rgba(186, 92, 255, 0.10);\n  color: #e0b1ff;\n  font-size: 7px;\n  font-weight: 950;\n  letter-spacing: 0.08em;\n}\n\n.satellite-layer-note--loading {\n  color: rgba(224, 177, 255, 0.82);\n}\n\n.satellite-layer-note--error {\n  color: #ff9595;\n}\n\n.satellite-candidate-popup {\n  min-width: 235px;\n  padding: 14px;\n}\n\n.satellite-candidate-popup__title {\n  margin-bottom: 10px;\n  color: #e0b1ff;\n  font-size: 10px;\n  font-weight: 950;\n  letter-spacing: 0.12em;\n}\n\n.satellite-candidate-popup__row {\n  display: grid;\n  grid-template-columns: 92px 1fr;\n  gap: 10px;\n  padding: 6px 0;\n  border-top: 1px solid rgba(224, 177, 255, 0.10);\n  font-size: 10px;\n}\n\n.satellite-candidate-popup__key {\n  color: rgba(232, 241, 247, 0.42);\n}\n\n.satellite-candidate-popup__value {\n  overflow-wrap: anywhere;\n  color: rgba(232, 241, 247, 0.92);\n  font-weight: 700;\n}\n\n.satellite-candidate-popup__disclaimer {\n  margin-top: 10px;\n  padding-top: 9px;\n  border-top: 1px solid rgba(224, 177, 255, 0.14);\n  color: rgba(224, 177, 255, 0.72);\n  font-size: 9px;\n  line-height: 1.45;\n}\n\n.detail-context-grid {\n  display: grid;\n  grid-template-columns: repeat(2, minmax(0, 1fr));\n  gap: 8px;\n}\n\n.detail-context-status {\n  margin-top: 8px;\n}\n\n@media (max-width: 720px) {\n  .detail-context-grid {\n    grid-template-columns: 1fr;\n  }\n}\n' + "\n"

def patch_vite(text: str) -> str:
    if "'/satellite':" in text:
        return text
    return _replace_once(
        text,
        "      '/ocean': {\n        target: 'http://127.0.0.1:8000',\n        changeOrigin: false,\n      },\n",
        "      '/ocean': {\n        target: 'http://127.0.0.1:8000',\n        changeOrigin: false,\n      },\n      '/satellite': {\n        target: 'http://127.0.0.1:8000',\n        changeOrigin: false,\n      },\n",
        "vite satellite proxy",
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

    if (
        "fetchSatelliteCandidates" in originals["main"]
        and 'id="satellite-layer-toggle"' in originals["index"]
        and "'/satellite':" in originals["vite"]
    ):
        print("SYSTEM-3 Web GIS MVP already installed; no edit applied.")
        return 0

    try:
        updated = {
            "main": patch_main(originals["main"]),
            "index": patch_index(originals["index"]),
            "i18n": patch_i18n(originals["i18n"]),
            "css": patch_css(originals["css"]),
            "vite": patch_vite(originals["vite"]),
        }

        # SYSTEM-3 runtime UX fixes validated in browser:
        # 1) show all demo events by default;
        # 2) auto-fit the tiny SAR candidate polygons when enabled.
        seven_checked = '<input type="radio" name="time-window" value="7" checked />'
        seven_plain = '<input type="radio" name="time-window" value="7" />'
        all_plain = '<input type="radio" name="time-window" value="all" />'
        all_checked = '<input type="radio" name="time-window" value="all" checked />'

        if seven_checked in updated["index"]:
            updated["index"] = updated["index"].replace(
                seven_checked,
                seven_plain,
                1,
            )

        if all_checked not in updated["index"] and all_plain in updated["index"]:
            updated["index"] = updated["index"].replace(
                all_plain,
                all_checked,
                1,
            )

        if "map.fitBounds(bounds" not in updated["main"]:
            source_marker = """    setGeoJSONSourceData(
      'satellite-candidates',
      payload,
    );

    setSatelliteLayerVisibility(true);
"""
            source_replacement = """    setGeoJSONSourceData(
      'satellite-candidates',
      payload,
    );

    if (payload.features.length) {
      const bounds = new maplibregl.LngLatBounds();

      for (const feature of payload.features) {
        const coords = feature.geometry.coordinates.flat(10);

        for (let i = 0; i < coords.length; i += 2) {
          bounds.extend([
            coords[i],
            coords[i + 1],
          ]);
        }
      }

      map.fitBounds(bounds, {
        padding: 120,
        maxZoom: 13,
        duration: 1200,
      });
    }

    setSatelliteLayerVisibility(true);
"""
            updated["main"] = _replace_once(
                updated["main"],
                source_marker,
                source_replacement,
                "satellite candidate auto-fit",
            )
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No existing frontend file was modified.")
        return 3

    backups = []
    for label, path in TARGETS.items():
        backups.append(_backup(path, f"frontend_{label}"))

    for key, path in TARGETS.items():
        path.write_text(updated[key], encoding="utf-8")

    print("SYSTEM-3 Web GIS MVP installed.")
    print("Modified:")
    print("  frontend/src/main.js")
    print("  frontend/index.html")
    print("  frontend/src/i18n.js")
    print("  frontend/src/style.css")
    print("  frontend/vite.config.js")
    print("Added modules:")
    print("  frontend/src/satellite.js")
    print("  frontend/src/monitorContext.js")
    print("Backups:")
    for backup in backups:
        print(f"  {backup.relative_to(REPO_ROOT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
