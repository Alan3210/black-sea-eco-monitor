# ЭкоКонтур Черноморья

**ЭкоКонтур Черноморья** — интеллектуальная система экологического мониторинга и прогнозирования для акватории Чёрного моря.

Проект объединяет экологические события, открытые данные наблюдений, океанографические поля, модели переноса и прогнозы загрязнений в единую систему с Web GIS и AR-клиентом.

## Что уже реализовано

### Экологические события

- сбор и нормализация событий из открытых источников;
- canonical Event Store;
- дедупликация и lifecycle событий;
- evidence и provenance;
- координаты, тип и качество локации;
- incident / detection / source time;
- FastAPI endpoints для событий и evidence.

Основные endpoints:

```text
GET /monitor/events/
GET /monitor/events/{event_id}
GET /monitor/events/{event_id}/evidence
```

### Океанографические данные

Подключён Copernicus Marine для поверхностных течений Чёрного моря.

Используемый продукт:

```text
BLKSEA_ANALYSISFORECAST_PHY_007_001
```

Основной dataset:

```text
cmems_mod_blk_phy-cur_anfc_2.5km_PT1H-m
```

API:

```text
GET /ocean/currents/
```

### OceanDrift

Реализован прогноз пассивного переноса частиц на поверхности моря.

API:

```text
GET /ocean/drift/
```

В Web GIS отображаются:

- облако частиц;
- средний трек;
- область распространения;
- прогнозные горизонты.

### OpenOil

OpenOil используется для моделирования нефтяного загрязнения.

В forcing входят:

- Copernicus currents;
- Copernicus waves / Stokes drift;
- Copernicus temperature;
- Copernicus salinity;
- ECMWF 10 m wind;
- NOAA ADIOS weathering.

Проведена standard validation matrix:

```text
24 сценария
3 региона:
- Novorossiysk nearshore
- Eastern Black Sea offshore
- Central Black Sea
```

Результат:

- 24/24 сценария завершены без ERROR / INCOMPLETE;
- nearshore-сценарии переходят в физическое terminal state `stranded`;
- offshore и central Black Sea проходят полный временной горизонт.

Текущий OpenOil контур остаётся инженерно-научным прототипом. Тяжёлые расчёты не запускаются синхронно из AR API.

### Web GIS

Frontend построен на MapLibre.

Реализованы:

- карта событий;
- фильтры;
- карточки событий и evidence;
- co-located grouping;
- data-quality UI;
- RU / EN;
- визуализация течений стрелками;
- particle currents;
- OceanDrift forecast;
- UX для долгих задач.

### AR Integration Layer

Добавлен Unity-friendly AR Scene API.

Endpoint:

```text
GET /api/ar/scene
```

AR Scene API v0.3 поддерживает:

- реальные incident-объекты из canonical Event Store;
- observer position;
- `distance_m`;
- `bearing_deg`;
- `max_distance_km`;
- cached/demo current;
- cached/demo OpenOil forecast.

Пример:

```text
GET /api/ar/scene?observer_lat=44.724&observer_lon=37.7691&max_distance_km=50
```

Unity-клиент не выполняет экологические расчёты. Backend является вычислительным ядром, а Unity — визуальным клиентом.

## Архитектура

```text
Open sources / environmental data
              ↓
        ingestion / agents
              ↓
       Canonical Event Store
              ↓
   models / forecasts / services
              ↓
            FastAPI
          ↙         ↘
      Web GIS      Unity AR
```

## Структура репозитория

```text
black-sea-eco-monitor/
├── agents/             # ingestion, event processing, ocean/model logic
├── backend/            # FastAPI, schemas, services, DB models
├── data/               # project data
├── database/           # canonical event storage
├── docs/               # project documentation
├── experiments/        # experimental work
├── frontend/           # MapLibre Web GIS
├── tests/              # automated tests
├── tools/              # maintenance / validation utilities
├── validation/         # local validation outputs, ignored by git
├── test-results/       # pytest outputs and test DB, ignored by git
├── debug-results/      # live/debug logs, ignored by git
└── dev-snapshots/      # temporary development snapshots, ignored by git
```

## Запуск backend

Из корня проекта:

```powershell
.\backend\venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Тесты

Полный backend regression:

```powershell
pytest -q *> test-results\pytest_result.txt
Get-Content test-results\pytest_result.txt -Tail 30
```

Текущий стабильный checkpoint:

```text
203 passed
```

AR test suite:

```powershell
pytest -q tests/test_ar_scene_builder.py tests/test_ar_scene_api.py tests/test_ar_scene_eventstore.py tests/test_ar_scene_geo.py tests/test_ar_scene_api_v03.py *> test-results\ar_scene_all_test.txt
```

Текущий AR checkpoint:

```text
15 passed
```

## Научная корректность

Проект различает:

- наблюдение;
- подтверждённое событие;
- модель;
- прогноз;
- data quality / provenance.

В частности:

- спутниковая аномалия не считается автоматически подтверждённым загрязнением;
- OpenOil/OpenDrift результаты маркируются как модельные;
- nearshore forcing может использовать ближайшую валидную океанскую ячейку, и такой сдвиг должен быть явно показан пользователю;
- terminal state `stranded` не трактуется как ошибка модели.

## Ближайший этап

Текущий приоритет — конференционный вертикальный срез:

```text
Environmental incident
        ↓
Event Store
        ↓
Ocean data / forecast
        ↓
FastAPI
        ↓
Unity AR
        ↓
Geo AR HUD on iPhone
```

AR-клиент разрабатывается отдельно на Unity 2022.3 LTS + AR Foundation для iPhone 11.

## Лицензия

См. `LICENSE`.
