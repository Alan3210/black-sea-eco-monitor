# ЭкоКонтур Черноморья — GEE Dataset Audit v0.1

Дата: 2026-09-17

## 1. Цель аудита

Выбрать спутниковые datasets Google Earth Engine, которые дают практическую ценность
для мониторинга Черного моря, и определить один первый MVP без расширения scope.

Главное правило:

```text
satellite observation != model forecast
SAR anomaly != confirmed oil spill
```

## 2. Shortlist

| Priority | Dataset | Main use case | Status |
|---|---|---|---|
| P0 | COPERNICUS/S1_GRD | SAR surface anomaly / slick candidate screening | selected for v0.1 |
| P1 | COPERNICUS/S2_SR_HARMONIZED | coastal water colour / turbidity proxies | later |
| P2 | COPERNICUS/S3/OLCI | regional ocean-colour context | later |
| P2 | NASA/LANCE/SNPP_VIIRS/C2 | active fire / heat anomaly evidence | later |
| Future | Sentinel-5P collections | atmospheric NO2 / SO2 context | not in first implementation |

Не интегрировать все datasets одновременно.

## 3. P0 — Sentinel-1 GRD

Earth Engine collection:

```text
COPERNICUS/S1_GRD
```

Роль:

- SAR scene discovery по AOI и времени;
- observation metadata;
- night/cloud-independent surface imaging;
- основа для будущего dark-spot anomaly screening;
- comparison layer рядом с EventStore / OceanDrift / OpenOil.

Не использовать Sentinel-1 observation как автоматическое подтверждение типа загрязнения.

### v0.1 query profile

```text
instrumentMode = IW
resolution_meters = 10
VV required
VH optional
```

Discovery допускает:

```text
ASCENDING
DESCENDING
```

Temporal before/after comparison должен по возможности использовать:

```text
same orbitProperties_pass
same relativeOrbitNumber_start
```

Это снижает различия, связанные с геометрией наблюдения.

### Required metadata

```text
scene_id
system_index
acquisition_time
platform_number
instrument_mode
polarizations
orbit_pass
relative_orbit
resolution_meters
footprint
```

## 4. Live validation — 2026-09-17

Проверено через Earth Engine Python API:

```text
earthengine-api = 1.7.43
ee.Initialize(project=...) = OK
AOI = Novorossiysk
bbox = [37.55, 44.55, 38.15, 44.95]
lookback = 30 days
dataset = COPERNICUS/S1_GRD
filter = IW + 10 m + VV
matching scenes = 31
saved metadata records = 5
```

Пример реально полученной scene metadata:

```text
acquisition_time = 2026-09-17T03:31:58Z
orbit_pass = DESCENDING
polarizations = VV, VH
relative_orbit = 21
resolution_meters = 10
```

Validation artifact:

```text
validation/gee_sentinel1_probe.json
```

Важно: scene footprint описывает геометрию satellite scene, а не только query AOI.
Для GIS later необходимо явно разделять `query_aoi` и `source_scene_footprint`.

## 5. Sentinel-1 scientific semantics

Разрешенные v0.1 термины:

```text
sar_anomaly
dark-spot candidate
possible surface slick
satellite-derived observation
```

Не использовать автоматически:

```text
oil spill confirmed
pollution confirmed
```

SAR dark area может иметь несколько причин.
До validated classifier результат остается screening/observation layer.

## 6. P1 — Sentinel-2 Surface Reflectance

Candidate collection:

```text
COPERNICUS/S2_SR_HARMONIZED
```

Potential use:

- coastal water colour;
- turbidity / suspended-matter anomaly proxies;
- plume boundaries;
- visual before/after comparison.

Potential QA companion:

```text
GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED
```

Статус:

```text
not live-validated in current checkpoint
not part of v0.1 implementation
```

До отдельной Black Sea validation нельзя выдавать произвольный spectral index
как физическую концентрацию chlorophyll-a, turbidity или pollutants.

## 7. P2 — Sentinel-3 OLCI

Candidate collection:

```text
COPERNICUS/S3/OLCI
```

Potential use:

- regional ocean-colour context;
- large-scale bloom / water anomaly context.

Статус:

```text
not live-validated in current checkpoint
not part of v0.1 implementation
```

На первом этапе использовать только как future dataset candidate.

## 8. P2 — VIIRS Active Fire

Candidate collection:

```text
NASA/LANCE/SNPP_VIIRS/C2
```

Potential use:

- active fire / heat anomaly evidence;
- linkage to industrial fire or wildfire events;
- regional context for smoke/fire incidents.

Статус:

```text
not live-validated in current checkpoint
not part of v0.1 implementation
```

Этот dataset не относится к первому marine pollution MVP.

## 9. Future — Sentinel-5P

Potential use:

- NO2 / SO2 atmospheric context;
- large industrial or fire episodes.

Статус:

```text
future Atmosphere Layer
not in current scope
```

## 10. Authentication architecture

Development:

```text
earthengine-api
ee.Authenticate()
ee.Initialize(project=GEE_PROJECT_ID)
```

Production later:

```text
Google Cloud Project
        ↓
Service Account / ADC
        ↓
Earth Engine API
```

Credentials never enter Git.

## 11. Storage / provenance requirements

Satellite observation metadata will be stored in:

```text
database/events.db
```

but in separate tables:

```text
satellite_observations
event_satellite_observations
```

Required provenance concepts:

```text
information_type = satellite_observation
derivation_level
sensor
dataset_id
source_image_id
acquisition_time
processing_time
processing_version
orbit_pass
relative_orbit
instrument_mode
polarizations
```

Raster products stay outside SQLite.

## 12. Conference value

Sentinel-1 gives the strongest first marine demo because it fits the existing vertical:

```text
Event
  ↓
OceanDrift / OpenOil
  ↓
Impact Forecast
  ↓
SatelliteObservation
  ↓
Web GIS
```

For reliability, conference mode should use precomputed/cached scenes rather than
triggering a heavy live Earth Engine processing job during the presentation.

## 13. Decision

Selected first dataset:

```text
COPERNICUS/S1_GRD
```

Selected first product:

```text
Sentinel-1 SAR Observation Layer v0.1
```

Other datasets remain roadmap items until the Sentinel-1 path is stable.
