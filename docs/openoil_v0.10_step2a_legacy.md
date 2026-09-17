# Black Sea Eco Monitor — OpenOil v0.10 Step 2A

This is the first actual OpenOil model execution in the project.

It deliberately separates **engine validation** from **operational forecasting**.

## What it validates

OpenOil runs with:

- real Copernicus current snapshot
- real Copernicus wave height
- real Copernicus Stokes drift
- real ECMWF 10 m wind snapshot
- NOAA ADIOS oil type / weathering
- evaporation
- emulsification
- dispersion
- oil mass-budget extraction

## Important scientific limitation

The environmental fields are sampled once at the start of the run and then held constant in space and time.

Therefore this step is:

```text
REAL OPENOIL ENGINE
+ REAL ENVIRONMENTAL SNAPSHOT
!= OPERATIONAL OIL-SPILL FORECAST
```

This is intentional.

The next step replaces the constant reader with full time/space readers and adds real Black Sea temperature and salinity.

## Install

Extract into:

```text
D:\repository\black-sea-eco-monitor
```

It adds:

```text
agents/ocean_data/openoil_validation.py
tests/test_openoil_validation.py
tools/check_openoil_validation.py
```

No API routes or frontend files are changed.

## Test

```powershell
cd D:\repository\black-sea-eco-monitor
.\backend\venv\Scripts\Activate.ps1

pytest -q *> pytest_openoil_v010_step2a.txt
Get-Content pytest_openoil_v010_step2a.txt -Tail 20
```

This step adds 6 tests.

With the current project checkpoint of 150 tests, expected total:

```text
156 passed
```

## First live OpenOil run

Use the same Novorossiysk scenario:

```powershell
python tools/check_openoil_validation.py --lon 37.7691 --lat 44.7240 --hours 6 --particles 100 --volume-m3 1 1> openoil_validation_live.txt 2> openoil_validation_sources.log

Get-Content openoil_validation_live.txt
```

The checker automatically uses the nearest valid ocean cell from the environmental-forcing stage so that a near-coast user point is not silently seeded on land.

## What we want to see

```text
OPENOIL V0.10 STEP 2A - ENGINE VALIDATION

Status: NOT_OPERATIONAL_FORECAST
Model: OpenOil
Weathering: NOAA ADIOS
Oil type: ...

FINAL POSITIONS
...

MASS BUDGET
remaining_oil_kg: ...
evaporated_kg: ...
dispersed_kg: ...
...
```

A non-zero evaporated or dispersed oil mass is useful confirmation that weathering physics is actually executing.

## If it fails

Send only:

```powershell
Get-Content openoil_validation_sources.log -Tail 80
```

## Next step

Step 2B will make the forcing dynamic:

- Copernicus hourly current grid
- Copernicus hourly wave/Stokes grid
- ECMWF wind through time
- Copernicus Black Sea temperature
- Copernicus Black Sea salinity

Only after that should the result be exposed to the user as an oil-spill forecast.
