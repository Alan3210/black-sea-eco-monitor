# Black Sea Eco Monitor Web v0.7.1 — Current Arrow Size

Adds an operator-controlled size slider for the Copernicus surface-current arrows.

## New
- Slider directly under the Surface currents layer.
- Range: 60% → 200%.
- Step: 10%.
- Changes arrow size instantly without reloading Copernicus data.
- Preference is saved in localStorage and restored after refresh.
- RU/EN localization.
- Existing speed-based relative sizing is preserved.

## Install
Copy over:
`D:\repository\black-sea-eco-monitor\frontend`

## Test
```powershell
npm test *> frontend_v071_test.txt
Get-Content frontend_v071_test.txt -Tail 15
```

Expected:
`29 passed`

## Build
```powershell
npm run build *> frontend_v071_build.txt
Get-Content frontend_v071_build.txt -Tail 20
```

Then restart the monitor.
