from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

INDEX = REPO_ROOT / "frontend" / "index.html"
DRIFT = REPO_ROOT / "frontend" / "src" / "drift.js"
MAIN = REPO_ROOT / "frontend" / "src" / "main.js"
I18N = REPO_ROOT / "frontend" / "src" / "i18n.js"
STYLE = REPO_ROOT / "frontend" / "src" / "style.css"
TEST = REPO_ROOT / "frontend" / "src" / "driftForcing.test.js"

MARKER = "WEATHER1_4_FORCING_MODE_UI"


TEST_CONTENT = r"""import {
  DEFAULT_DRIFT_FORCING_MODE,
  DRIFT_FORCING_CURRENT_ONLY,
  DRIFT_FORCING_CURRENTS_PLUS_WIND,
  driftApiUrl,
  driftForcingViewModel,
  normalizeDriftForcingMode,
} from './drift.js';


describe('WEATHER-1.4 drift forcing mode', () => {
  it('keeps current_only as the default', () => {
    expect(DEFAULT_DRIFT_FORCING_MODE)
      .toBe(DRIFT_FORCING_CURRENT_ONLY);
    expect(normalizeDriftForcingMode(null))
      .toBe(DRIFT_FORCING_CURRENT_ONLY);
  });


  it('accepts the operational currents_plus_wind mode', () => {
    expect(
      normalizeDriftForcingMode('currents_plus_wind'),
    ).toBe(DRIFT_FORCING_CURRENTS_PLUS_WIND);
  });


  it('falls back safely for an unknown mode', () => {
    expect(
      normalizeDriftForcingMode('unknown-mode'),
    ).toBe(DRIFT_FORCING_CURRENT_ONLY);
  });


  it('sends current_only explicitly in the API URL by default', () => {
    const url = new URL(
      driftApiUrl({
        longitude: 37.8,
        latitude: 44.6,
        hours: 6,
        particles: 100,
      }),
      'http://localhost',
    );

    expect(url.searchParams.get('forcing_mode'))
      .toBe('current_only');
  });


  it('sends currents_plus_wind explicitly in the API URL', () => {
    const url = new URL(
      driftApiUrl({
        longitude: 37.8,
        latitude: 44.6,
        hours: 6,
        particles: 100,
        forcingMode: DRIFT_FORCING_CURRENTS_PLUS_WIND,
      }),
      'http://localhost',
    );

    expect(url.searchParams.get('forcing_mode'))
      .toBe('currents_plus_wind');
  });


  it('exposes ECMWF provenance and 2 percent windage', () => {
    const view = driftForcingViewModel(
      {
        forcing_mode: 'currents_plus_wind',
        simulation: {
          wind_drift_factor: 0.02,
        },
        forcing: {
          wind: {
            provider: 'ecmwf',
            model: 'ifs',
            forecast_reference_time:
              '2026-09-19T00:00:00+00:00',
            sources: ['google'],
            fallback_used: false,
          },
        },
      },
      DRIFT_FORCING_CURRENT_ONLY,
    );

    expect(view.windEnabled).toBe(true);
    expect(view.windDriftFactor).toBe(0.02);
    expect(view.provider).toBe('ecmwf');
    expect(view.model).toBe('ifs');
    expect(view.sources).toEqual(['google']);
    expect(view.forecastReferenceTime)
      .toBe('2026-09-19T00:00:00+00:00');
  });
});
"""


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly 1 marker, found {count}"
        )

    return text.replace(old, new, 1)


def backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    target = (
        BACKUP_DIR
        / f"{label}.before_weather1_4_{stamp}{path.suffix}"
    )
    shutil.copy2(path, target)
    return target


def patch_drift(text: str) -> str:
    if MARKER in text:
        return text

    constants_old = """export const DEFAULT_DRIFT_HORIZON = 24;
export const DEFAULT_DRIFT_PARTICLES = 300;
export const DEFAULT_DRIFT_RADIUS_M = 500;
export const DEFAULT_DRIFT_DIFFUSIVITY_M2_S = 2;
"""

    constants_new = """export const DEFAULT_DRIFT_HORIZON = 24;
export const DEFAULT_DRIFT_PARTICLES = 300;
export const DEFAULT_DRIFT_RADIUS_M = 500;
export const DEFAULT_DRIFT_DIFFUSIVITY_M2_S = 2;

// WEATHER1_4_FORCING_MODE_UI
export const DRIFT_FORCING_CURRENT_ONLY = 'current_only';
export const DRIFT_FORCING_CURRENTS_PLUS_WIND =
  'currents_plus_wind';
export const DEFAULT_DRIFT_FORCING_MODE =
  DRIFT_FORCING_CURRENT_ONLY;
export const DEFAULT_DRIFT_WINDAGE_FACTOR = 0.02;
"""

    text = replace_once(
        text,
        constants_old,
        constants_new,
        "drift forcing constants",
    )

    api_marker = """export function driftApiUrl({
  longitude,
  latitude,
"""

    helpers = """export function normalizeDriftForcingMode(
  value,
  fallback = DEFAULT_DRIFT_FORCING_MODE,
) {
  const normalized = String(value ?? '')
    .trim()
    .toLowerCase();

  if (
    normalized === DRIFT_FORCING_CURRENT_ONLY
    || normalized === DRIFT_FORCING_CURRENTS_PLUS_WIND
  ) {
    return normalized;
  }

  return fallback;
}


export function driftForcingViewModel(
  payload,
  requestedMode = DEFAULT_DRIFT_FORCING_MODE,
) {
  const requested = normalizeDriftForcingMode(
    requestedMode,
  );
  const mode = normalizeDriftForcingMode(
    payload?.forcing_mode,
    requested,
  );
  const windEnabled =
    mode === DRIFT_FORCING_CURRENTS_PLUS_WIND;
  const wind = windEnabled
    ? payload?.forcing?.wind
    : null;

  const payloadWindFactor = finiteNumber(
    payload?.simulation?.wind_drift_factor,
  );

  const sources = Array.isArray(wind?.sources)
    ? wind.sources
      .map((value) => String(value).trim())
      .filter(Boolean)
    : [];

  return {
    mode,
    windEnabled,
    windDriftFactor: windEnabled
      ? (
        payloadWindFactor
        ?? DEFAULT_DRIFT_WINDAGE_FACTOR
      )
      : 0,
    provider: wind?.provider ?? null,
    model: wind?.model ?? null,
    forecastReferenceTime:
      wind?.forecast_reference_time ?? null,
    sources,
    fallbackUsed: Boolean(wind?.fallback_used),
  };
}


""" + api_marker

    text = replace_once(
        text,
        api_marker,
        helpers,
        "drift forcing helpers",
    )

    signature_old = """  particles = DEFAULT_DRIFT_PARTICLES,
  radiusM = DEFAULT_DRIFT_RADIUS_M,
  diffusivityM2S = DEFAULT_DRIFT_DIFFUSIVITY_M2_S,
}) {
"""
    signature_new = """  particles = DEFAULT_DRIFT_PARTICLES,
  radiusM = DEFAULT_DRIFT_RADIUS_M,
  diffusivityM2S = DEFAULT_DRIFT_DIFFUSIVITY_M2_S,
  forcingMode = DEFAULT_DRIFT_FORCING_MODE,
}) {
"""
    text = replace_once(
        text,
        signature_old,
        signature_new,
        "drift API forcing argument",
    )

    params_old = """    lat: String(Number(latitude)),
    hours: String(
"""
    params_new = """    lat: String(Number(latitude)),
    forcing_mode: normalizeDriftForcingMode(
      forcingMode,
    ),
    hours: String(
"""
    text = replace_once(
        text,
        params_old,
        params_new,
        "drift API forcing query",
    )

    return text


def patch_main(text: str) -> str:
    if MARKER in text:
        return text

    import_old = """import {
  DEFAULT_DRIFT_HORIZON,
  DEFAULT_DRIFT_PARTICLES,
"""
    import_new = """import {
  DEFAULT_DRIFT_FORCING_MODE,
  DEFAULT_DRIFT_HORIZON,
  DEFAULT_DRIFT_PARTICLES,
  DRIFT_FORCING_CURRENTS_PLUS_WIND,
"""
    text = replace_once(
        text,
        import_old,
        import_new,
        "main drift import constants",
    )

    import_helper_old = """  driftEnvelopeGeoJSON,
  driftPointsGeoJSON,
  driftSeedGeoJSON,
"""
    import_helper_new = """  driftEnvelopeGeoJSON,
  driftForcingViewModel,
  driftPointsGeoJSON,
  driftSeedGeoJSON,
"""
    text = replace_once(
        text,
        import_helper_old,
        import_helper_new,
        "main drift view model import",
    )

    import_normalizer_old = """  fetchDriftForecast,
  normalizeDriftHorizon,
"""
    import_normalizer_new = """  fetchDriftForecast,
  normalizeDriftForcingMode,
  normalizeDriftHorizon,
"""
    text = replace_once(
        text,
        import_normalizer_old,
        import_normalizer_new,
        "main forcing normalizer import",
    )

    storage_old = """const DRIFT_HORIZON_STORAGE_KEY =
  'black-sea-eco-monitor.drift-horizon';

const DRIFT_PARTICLES_STORAGE_KEY =
"""
    storage_new = """const DRIFT_HORIZON_STORAGE_KEY =
  'black-sea-eco-monitor.drift-horizon';

// WEATHER1_4_FORCING_MODE_UI
const DRIFT_FORCING_MODE_STORAGE_KEY =
  'black-sea-eco-monitor.drift-forcing-mode';

const DRIFT_PARTICLES_STORAGE_KEY =
"""
    text = replace_once(
        text,
        storage_old,
        storage_new,
        "main forcing storage key",
    )

    dom_old = """const driftRunButton = document.getElementById(
  'drift-run',
);
const driftHorizonInputs = [
"""
    dom_new = """const driftRunButton = document.getElementById(
  'drift-run',
);
const driftForcingInputs = [
  ...document.querySelectorAll(
    'input[name="drift-forcing-mode"]',
  ),
];
const driftForcingDetails = document.getElementById(
  'drift-forcing-details',
);
const driftScopeNote = document.getElementById(
  'drift-scope-note',
);
const driftHorizonInputs = [
"""
    text = replace_once(
        text,
        dom_old,
        dom_new,
        "main forcing DOM refs",
    )

    state_old = """let driftHorizon = normalizeDriftHorizon(
  window.localStorage.getItem(
    DRIFT_HORIZON_STORAGE_KEY,
  ),
"""
    state_new = """let driftForcingMode = normalizeDriftForcingMode(
  window.localStorage.getItem(
    DRIFT_FORCING_MODE_STORAGE_KEY,
  ),
  DEFAULT_DRIFT_FORCING_MODE,
);

let driftHorizon = normalizeDriftHorizon(
  window.localStorage.getItem(
    DRIFT_HORIZON_STORAGE_KEY,
  ),
"""
    text = replace_once(
        text,
        state_old,
        state_new,
        "main forcing state",
    )

    render_start_old = """function renderDriftControls() {
  for (const input of driftHorizonInputs) {
"""
    render_start_new = """function renderDriftControls() {
  for (const input of driftForcingInputs) {
    input.checked = input.value === driftForcingMode;
    input.disabled = driftLoading;
  }

  for (const input of driftHorizonInputs) {
"""
    text = replace_once(
        text,
        render_start_old,
        render_start_new,
        "main forcing control rendering",
    )

    details_anchor_old = """  if (driftParticlesValue) {
    driftParticlesValue.textContent = String(driftParticles);
  }

  if (driftCoordinate) {
"""
    details_anchor_new = """  if (driftParticlesValue) {
    driftParticlesValue.textContent = String(driftParticles);
  }

  const forcingView = driftForcingViewModel(
    driftPayload,
    driftForcingMode,
  );
  const windagePercent = Math.round(
    forcingView.windDriftFactor * 100,
  );

  if (driftForcingDetails) {
    if (!forcingView.windEnabled) {
      driftForcingDetails.textContent = t(
        currentLanguage,
        'drift.forcingCurrentSummary',
      );
    } else if (
      forcingView.forecastReferenceTime
    ) {
      const source = forcingView.sources.length
        ? forcingView.sources.join(', ')
        : 'ECMWF';

      driftForcingDetails.textContent = t(
        currentLanguage,
        'drift.forcingWindReady',
        {
          run: formatCurrentValidTime(
            forcingView.forecastReferenceTime,
            localeForLanguage(currentLanguage),
          ),
          source,
          windage: windagePercent,
        },
      );
    } else {
      driftForcingDetails.textContent = t(
        currentLanguage,
        'drift.forcingWindPlanned',
        {
          windage: windagePercent,
        },
      );
    }
  }

  if (driftScopeNote) {
    driftScopeNote.textContent = t(
      currentLanguage,
      forcingView.windEnabled
        ? 'drift.scopeCurrentsWind'
        : 'drift.scopeCurrentOnly',
      {
        windage: windagePercent,
      },
    );
  }

  if (driftCoordinate) {
"""
    text = replace_once(
        text,
        details_anchor_old,
        details_anchor_new,
        "main forcing provenance rendering",
    )

    fetch_old = """      hours: driftHorizon,
      particles: driftParticles,
    });
"""
    fetch_new = """      hours: driftHorizon,
      particles: driftParticles,
      forcingMode: driftForcingMode,
    });
"""
    text = replace_once(
        text,
        fetch_old,
        fetch_new,
        "main forcing API request",
    )

    listener_anchor = """for (const input of driftHorizonInputs) {
  input.addEventListener('change', () => {
"""
    listener_new = """for (const input of driftForcingInputs) {
  input.addEventListener('change', () => {
    if (!input.checked) return;

    const nextMode = normalizeDriftForcingMode(
      input.value,
    );

    if (nextMode === driftForcingMode) {
      renderDriftControls();
      return;
    }

    driftForcingMode = nextMode;

    window.localStorage.setItem(
      DRIFT_FORCING_MODE_STORAGE_KEY,
      driftForcingMode,
    );

    // A forecast calculated with different physical forcing must
    // never remain active after the user switches forcing mode.
    if (driftPayload) {
      driftPayload = null;
      driftForecastSourceEventId = null;
      clearImpactScreening();
      clearDriftMapData({ keepSeed: true });
    }

    renderDriftControls();
    refreshSelectedPanel();
  });
}


for (const input of driftHorizonInputs) {
  input.addEventListener('change', () => {
"""
    text = replace_once(
        text,
        listener_anchor,
        listener_new,
        "main forcing change listener",
    )

    return text


def patch_index(text: str) -> str:
    if 'id="drift-forcing-details"' in text:
        return text

    anchor = """              <div id="drift-coordinate" class="drift-coordinate">—</div>

              <div class="current-size-control__header drift-control__subhead" data-i18n="drift.horizon">
"""
    replacement = """              <div id="drift-coordinate" class="drift-coordinate">—</div>

              <div class="current-size-control__header drift-control__subhead" data-i18n="drift.forcing">
                Физическое воздействие
              </div>

              <div
                class="drift-horizon-grid drift-forcing-grid"
                role="radiogroup"
                aria-label="Режим внешнего воздействия прогноза дрейфа"
                data-i18n-aria-label="drift.forcingAria"
              >
                <label>
                  <input
                    type="radio"
                    name="drift-forcing-mode"
                    value="current_only"
                    checked
                  />
                  <span data-i18n="drift.forcingCurrentOnly">
                    Только течения
                  </span>
                </label>
                <label>
                  <input
                    type="radio"
                    name="drift-forcing-mode"
                    value="currents_plus_wind"
                  />
                  <span data-i18n="drift.forcingCurrentsWind">
                    Течения + ветер
                  </span>
                </label>
              </div>

              <div
                id="drift-forcing-details"
                class="filter-note drift-forcing-details"
                aria-live="polite"
              >
                Copernicus Marine · поверхностные течения · windage 0%
              </div>

              <div class="current-size-control__header drift-control__subhead" data-i18n="drift.horizon">
"""
    text = replace_once(
        text,
        anchor,
        replacement,
        "index forcing selector",
    )

    scope_old = """              <div class="filter-note drift-scope-note" data-i18n="drift.scopeNote">
                Модель переноса по поверхностным течениям. Ветер, волны и weathering нефти пока не учитываются.
              </div>
"""
    scope_new = """              <div
                id="drift-scope-note"
                class="filter-note drift-scope-note"
                data-i18n="drift.scopeCurrentOnly"
              >
                Пассивный поверхностный трассер: только течения. Ветер, волны/Stokes drift и weathering нефти не учитываются.
              </div>
"""
    text = replace_once(
        text,
        scope_old,
        scope_new,
        "index dynamic scope note",
    )

    return text


def patch_i18n(text: str) -> str:
    if "'drift.forcingCurrentsWind':" in text:
        return text

    ru_anchor = """    'drift.clear': 'Очистить',
"""
    ru_new = """    'drift.clear': 'Очистить',
    'drift.forcing': 'Физическое воздействие',
    'drift.forcingAria': 'Режим внешнего воздействия прогноза дрейфа',
    'drift.forcingCurrentOnly': 'Только течения',
    'drift.forcingCurrentsWind': 'Течения + ветер',
    'drift.forcingCurrentSummary': 'Copernicus Marine · поверхностные течения · windage 0%',
    'drift.forcingWindPlanned': 'Copernicus Marine + ECMWF IFS 10 м · прямой ветровой снос (windage) {windage}%',
    'drift.forcingWindReady': 'ECMWF IFS · run {run} · зеркало {source} · прямой windage {windage}%',
    'drift.scopeCurrentOnly': 'Пассивный поверхностный трассер: только течения. Ветер, волны/Stokes drift и weathering нефти не учитываются.',
    'drift.scopeCurrentsWind': 'Пассивный поверхностный трассер: течения + прямой windage {windage}%. Волны/Stokes drift и weathering нефти не учитываются; это не полноценный прогноз разлива нефти.',
"""
    text = replace_once(
        text,
        ru_anchor,
        ru_new,
        "RU forcing translations",
    )

    en_anchor = """    'drift.clear': 'Clear',
"""
    en_new = """    'drift.clear': 'Clear',
    'drift.forcing': 'Physical forcing',
    'drift.forcingAria': 'Drift forecast environmental forcing mode',
    'drift.forcingCurrentOnly': 'Currents only',
    'drift.forcingCurrentsWind': 'Currents + wind',
    'drift.forcingCurrentSummary': 'Copernicus Marine · surface currents · windage 0%',
    'drift.forcingWindPlanned': 'Copernicus Marine + ECMWF IFS 10 m · direct windage {windage}%',
    'drift.forcingWindReady': 'ECMWF IFS · run {run} · mirror {source} · direct windage {windage}%',
    'drift.scopeCurrentOnly': 'Passive surface tracer driven by currents only. Wind, waves/Stokes drift and oil weathering are excluded.',
    'drift.scopeCurrentsWind': 'Passive surface tracer with currents + direct {windage}% windage. Waves/Stokes drift and oil weathering are excluded; this is not a full oil-spill forecast.',
"""
    text = replace_once(
        text,
        en_anchor,
        en_new,
        "EN forcing translations",
    )

    return text


def patch_style(text: str) -> str:
    if ".drift-forcing-details {" in text:
        return text

    anchor = """.drift-horizon-grid input:checked + span {
  border-color: rgba(255, 166, 0, 0.42);
  background: rgba(255, 138, 0, 0.11);
  color: #ffe08a;
}

.drift-particle-control { margin-top: 8px; }
"""
    replacement = """.drift-horizon-grid input:checked + span {
  border-color: rgba(255, 166, 0, 0.42);
  background: rgba(255, 138, 0, 0.11);
  color: #ffe08a;
}

/* WEATHER1_4_FORCING_MODE_UI */
.drift-forcing-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 4px;
}

.drift-forcing-grid span {
  min-height: 30px;
  display: grid;
  place-items: center;
  line-height: 1.2;
}

.drift-forcing-details {
  margin-top: 6px;
  padding: 6px 8px;
  border: 1px solid rgba(143, 232, 243, 0.10);
  border-radius: 7px;
  background: rgba(7, 20, 29, 0.38);
  color: rgba(191, 235, 241, 0.62);
  font-size: 8px;
  line-height: 1.45;
}

.drift-particle-control { margin-top: 8px; }
"""
    return replace_once(
        text,
        anchor,
        replacement,
        "forcing CSS",
    )


def main() -> int:
    prerequisites = [
        INDEX,
        DRIFT,
        MAIN,
        I18N,
        STYLE,
    ]

    for path in prerequisites:
        if not path.exists():
            print(f"ERROR: prerequisite missing: {path}")
            return 2

    original = {
        INDEX: INDEX.read_text(encoding="utf-8"),
        DRIFT: DRIFT.read_text(encoding="utf-8"),
        MAIN: MAIN.read_text(encoding="utf-8"),
        I18N: I18N.read_text(encoding="utf-8"),
        STYLE: STYLE.read_text(encoding="utf-8"),
    }

    if (
        MARKER in original[DRIFT]
        and MARKER in original[MAIN]
        and 'id="drift-forcing-details"' in original[INDEX]
    ):
        if not TEST.exists():
            TEST.write_text(
                TEST_CONTENT,
                encoding="utf-8",
            )
        print("WEATHER-1.4 Web GIS forcing mode UI already installed.")
        return 0

    try:
        updated = {
            INDEX: patch_index(original[INDEX]),
            DRIFT: patch_drift(original[DRIFT]),
            MAIN: patch_main(original[MAIN]),
            I18N: patch_i18n(original[I18N]),
            STYLE: patch_style(original[STYLE]),
        }
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No frontend runtime file was modified.")
        return 3

    backups = []
    for path in prerequisites:
        backups.append(
            backup(
                path,
                path.stem.replace(".", "_"),
            )
        )

    for path, content in updated.items():
        path.write_text(
            content,
            encoding="utf-8",
        )

    TEST.write_text(
        TEST_CONTENT,
        encoding="utf-8",
    )

    print("WEATHER-1.4 Web GIS Forcing Mode UI v0.1 installed.")
    print("Modified:")
    print("  frontend/index.html")
    print("  frontend/src/drift.js")
    print("  frontend/src/main.js")
    print("  frontend/src/i18n.js")
    print("  frontend/src/style.css")
    print("Added:")
    print("  frontend/src/driftForcing.test.js")
    print("Behavior:")
    print("  current_only remains the default")
    print("  currents_plus_wind is selectable in Web GIS")
    print("  UI shows ECMWF provenance and direct windage")
    print("  mode changes invalidate prior drift/impact results")
    print("Backups:")
    for item in backups:
        print(f"  {item.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
