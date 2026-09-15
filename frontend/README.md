# Black Sea Eco Monitor Web — v0.6

Adds full operator-interface localization with an RU / EN switch.

## New in v0.6

- Russian is the default interface language.
- RU / EN switch in the top bar.
- Selected language is persisted in browser local storage.
- Static UI labels, filters, categories, statuses, severity, legends, panel labels,
  connection state, grouped incident UI, evidence actions, coordinate-quality notes,
  and canonical location names are localized.
- Dates and clock formatting follow the selected locale.
- Canonical event/source content is not machine-translated: source headlines and source
  names stay exactly as provided by the Monitor API.
- Map control tooltips are localized too.
- Data Quality UI from v0.5 remains intact.

Run:

```powershell
npm test
npm run build
```

Expected tests: 22 passed.

Then launch with the project-level launcher:

```text
START_MONITOR.cmd
```

Verify:
1. Russian is selected on first load.
2. Switching to EN updates the interface immediately.
3. Reloading the page preserves the selected language.
4. Open event/group panels in both languages.
