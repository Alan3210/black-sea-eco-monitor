# ЭкоКонтур Черноморья — Google Earth Engine Integration Plan v0.1

Дата: 2026-09-17

## 1. Цель

Интегрировать Google Earth Engine (GEE) как отдельный спутниковый аналитический слой проекта
«ЭкоКонтур Черноморья», не смешивая спутниковые наблюдения с модельными прогнозами и
canonical environmental events.

Главный принцип:

```text
Event != SatelliteObservation != ModelForecast
```

Дополнительное научное ограничение:

```text
SAR anomaly != confirmed oil spill
```

## 2. Роль GEE в архитектуре

```text
News / EventStore
        │
        ├──────────────────────┐
        │                      │
        ▼                      ▼
Copernicus Marine       Google Earth Engine
        │                      │
        ▼                      ▼
OceanDrift / OpenOil    Satellite Analytics
        │                      │
        └──────────┬───────────┘
                   ▼
             Impact / Fusion
                   ▼
             FastAPI / Web GIS
                   ▼
                  AR
```

GEE не заменяет Copernicus Marine, OceanDrift или OpenOil.

- моделирование отвечает: «куда может переместиться загрязнение»;
- satellite observation отвечает: «что наблюдалось спутниковым сенсором»;
- Impact отвечает: «какие известные объекты потенциально находятся в зоне воздействия».

## 3. Первый satellite MVP

Первый и единственный P0 для v0.1:

```text
Sentinel-1 SAR Observation Layer
Dataset: COPERNICUS/S1_GRD
```

Профиль:

```text
instrumentMode = IW
resolution_meters = 10
VV required
VH optional
ASCENDING + DESCENDING allowed for discovery
same orbit pass + same relative orbit required for temporal comparison
```

Назначение:

- получение доступных Sentinel-1 scenes по AOI и времени;
- получение metadata и provenance;
- подготовка cached observation layer;
- последующий SAR dark-anomaly screening как отдельный этап.

Не входит в первый checkpoint:

- автоматическое подтверждение нефтеразлива;
- AI oil/not-oil classification;
- real-time operational monitoring;
- одновременная интеграция Sentinel-2 / Sentinel-3 / VIIRS.

## 4. Подтвержденный Access Probe checkpoint

На 2026-09-17 live-проверено:

```text
earthengine-api = 1.7.43
ee.Initialize(project=...) = OK
dataset = COPERNICUS/S1_GRD
AOI = Novorossiysk
window = 30 days
filter = IW + 10 m + VV
matching scenes = 31
saved metadata records = 5
```

Probe:

```text
tools/gee_access_probe.py
```

Validation output:

```text
validation/gee_sentinel1_probe.json
```

Probe не изменяет FastAPI, EventStore и production database.

## 5. Backend boundary

GEE-код размещается в существующем service layer:

```text
backend/services/satellite/
    gee_client.py
    sentinel1.py
    observation_builder.py
    cache.py
```

Не вводить новый верхнеуровневый `agents/` layer только ради GEE.

FastAPI отвечает за API и orchestration.
Тяжёлый satellite processing не должен выполняться синхронно внутри frontend request.

## 6. Authentication

### Development

```python
import ee

ee.Authenticate()
ee.Initialize(project="GCP_PROJECT_ID")
```

Project ID передается через environment:

```text
GEE_PROJECT_ID
```

### Production / demo server later

Предпочтительно:

```text
Google Cloud Project
        ↓
Service Account / Application Default Credentials
        ↓
Earth Engine API
```

Credentials и service-account keys не хранить в Git.

## 7. Storage decision v0.1

Используется существующая SQLite database:

```text
database/events.db
```

Но satellite данные физически и логически изолируются отдельными таблицами:

```text
satellite_observations
event_satellite_observations
```

Не добавлять SAR-специфичные поля в таблицу `events`.

Связь event ↔ satellite observation — many-to-many.

```text
events
   │
   ▼
event_satellite_observations
   │
   ▼
satellite_observations
```

Тяжёлые raster assets (GeoTIFF, PNG preview, tiles) не хранить BLOB-ами в SQLite.
В БД хранить только metadata, geometry/provenance и cache reference.

## 8. SatelliteObservation semantic contract

Обязательные поля концептуального уровня:

```text
information_type
derivation_level
observation_type
sensor
dataset_id
source_image_id
acquisition_time
processing_time
geometry
confidence
review_status
processing_version
provenance
created_at
updated_at
```

### information_type

Для satellite layer:

```text
satellite_observation
```

Для model outputs:

```text
model_forecast
```

Для event evidence:

```text
event_evidence
```

Frontend не должен угадывать тип информации по endpoint или имени слоя.

### derivation_level

```text
raw
processed
derived
```

Sentinel-1 GRD scene metadata / prepared scene:

```text
processed
```

SAR anomaly polygon:

```text
derived
```

### Confidence semantics

`confidence` для SAR anomaly означает уверенность алгоритма в наличии выделенной аномалии.

Он НЕ означает вероятность того, что аномалия является нефтью.

### review_status

Базовые значения:

```text
unreviewed
review_required
reviewed
rejected
```

В v0.1 не использовать статус `confirmed_oil`.

## 9. Time semantics

Не использовать универсальный `timestamp`.

Satellite:

```text
acquisition_time
processing_time
created_at
```

Forecast:

```text
reference_time
valid_time
horizon_hours
```

Event evidence:

```text
incident_time
detection_time
source_time
```

## 10. Provenance

Критические поля должны быть обычными полями, а не только JSON:

```text
sensor
dataset_id
source_image_id
acquisition_time
processing_version
```

Расширенный provenance может храниться в `provenance_json`.

Пример:

```json
{
  "data_provider": "Copernicus Sentinel-1",
  "processing_platform": "Google Earth Engine",
  "dataset_id": "COPERNICUS/S1_GRD",
  "source_level": "GRD",
  "orbit_pass": "DESCENDING",
  "relative_orbit": 21,
  "instrument_mode": "IW",
  "polarizations": ["VV", "VH"],
  "processing_method": "sar_anomaly_screening",
  "processing_version": "0.1"
}
```

## 11. Cache strategy

GEE не должен вызываться на каждый frontend request.

Правильная схема:

```text
manual/scheduled satellite job
        ↓
Google Earth Engine
        ↓
normalized observation
        ↓
cache / database
        ↓
FastAPI
        ↓
Web GIS / AR
```

Conference demo использует precomputed/cached satellite scenarios.

Cache identity для processed observation:

```text
dataset_id
source_image_id
processing_version
ROI
```

## 12. API boundary

Первый production API не должен раскрывать внутреннюю технологию GEE как часть внешнего контракта.

Предпочтительно:

```text
GET /satellite/status
GET /satellite/scenes
GET /satellite/observations
```

Тяжёлый update/process endpoint — только после появления background job architecture.

## 13. Приоритеты dataset integration

```text
P0  Sentinel-1 SAR
P1  Sentinel-2 Surface Reflectance
P2  Sentinel-3 OLCI
P2  VIIRS Active Fire
Future  Sentinel-5P Atmosphere
```

В v0.1 реализуется только P0.

## 14. Conference MVP

Минимальный демонстрационный сценарий:

```text
Event
  ↓
EventStore
  ↓
OceanDrift / OpenOil forecast
  ↓
Impact Forecast
  ↓
cached Sentinel-1 observation
  ↓
SAR candidate / metadata layer
  ↓
Web GIS
```

AR не должен обращаться к GEE напрямую.

## 15. Scientific safeguards

Разрешенная терминология:

```text
SAR anomaly
dark-spot candidate
possible surface slick
satellite-derived observation
```

Запрещено без независимого подтверждения:

```text
oil confirmed by satellite
confirmed spill
confirmed ecological damage
```

Корреляция между Event, Forecast и SatelliteObservation не равна подтверждению причинной связи.

## 16. v0.1 acceptance criteria

### Access checkpoint — завершен

```text
[x] earthengine-api installed
[x] ee.Initialize(project=...) works
[x] Novorossiysk / Black Sea AOI query works
[x] Sentinel-1 recent metadata retrieved
[x] IW + 10 m + VV filtering works
[x] compact provenance JSON generated
```

### Следующий implementation checkpoint

```text
[ ] SatelliteObservation schema
[ ] satellite_observations table
[ ] event_satellite_observations table
[ ] offline unit tests
[ ] no live GEE dependency in normal regression
[ ] read-only satellite API
[ ] cached demo scene
[ ] Web GIS satellite layer
```

Sentinel-2, Sentinel-3 и VIIRS не являются acceptance criteria v0.1.

## 17. Следующая последовательность

```text
Access Probe (done)
        ↓
SatelliteObservation schema/store
        ↓
read-only Satellite Catalog/API
        ↓
cached Sentinel-1 scene
        ↓
SAR candidate prototype
        ↓
Web GIS overlay
        ↓
Event / Forecast fusion
```
