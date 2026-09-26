ЭкоКонтур Черноморья — Impact Forecast v0.1

Пакет добавляет:
- backend/schemas/impact.py
- backend/services/impact_service.py
- backend/api/impact.py
- tools/install_impact_v01.py
- tests/test_impact_service.py
- tests/test_impact_api.py
- docs/IMPACT_FORECAST_V01.md
- Samples/impact_demo_request.json

Шаг 1 — распаковать архив в корень:
D:\repository\black-sea-eco-monitor

Шаг 2 — безопасный dry-run:
python tools/install_impact_v01.py

Ожидаемо:
DRY RUN
backend/main.py can be patched safely.
No files changed.

Шаг 3 — применить router patch:
python tools/install_impact_v01.py --apply

Шаг 4 — новые тесты:
pytest -q tests/test_impact_service.py tests/test_impact_api.py *> test-results\impact_v01_test.txt
Get-Content test-results\impact_v01_test.txt -Tail 30

Ожидаемо:
8 passed

Шаг 5 — полный regression:
pytest -q *> test-results\pytest_result.txt
Get-Content test-results\pytest_result.txt -Tail 30

Текущий checkpoint до Impact v0.1: 212 passed.
После добавления 8 новых тестов ожидаемо:
220 passed

Шаг 6 — Swagger:
http://127.0.0.1:8000/docs

Новые endpoints:
GET  /impact/targets
POST /impact/drift
