# Executive Summary

The following is a step-by-step guide to add a new `TECHNICAL_PASSPORT.md` in `docs/architecture` of the **black-sea-eco-monitor** repository. It covers creating the directory (if needed), writing the file with full content (including an executive summary), ensuring UTF-8 encoding with LF endings, staging and committing with a Conventional Commit message, and safely pushing to `origin/main`. It also shows how to verify the file on the remote, compute its SHA-256 hash, and how to revert the changes if necessary. All commands are given in both Windows PowerShell and POSIX shells, with expected outputs and checks. Wherever applicable, commit conventions and file-encoding details are cited from authoritative sources.

## 1. Prepare the Git branch

Ensure you are on `main`, have a clean working tree, and the remote is up to date:

- **PowerShell (Windows)**:
  ```powershell
  # Check current branch and status
  git rev-parse --abbrev-ref HEAD
  git status
  ```
- **POSIX (Linux/Mac)**:
  ```bash
  git rev-parse --abbrev-ref HEAD
  git status
  ```

**Expected:** The branch name should be `main`, and `git status` should report “working tree clean” and “nothing to commit”. If you’re on a different branch, switch to main:

```bash
git checkout main
git pull --ff-only
```

Make sure your local `main` is up-to-date with `origin/main`:

```bash
git fetch
git log --oneline origin/main..main
```

If the fetch shows new commits on `origin/main`, merge or rebase them first (`git pull --rebase` or resolve as needed) before proceeding.

## 2. Create the directory

Create the `docs/architecture` directory (if it doesn’t exist):

- **PowerShell**:
  ```powershell
  # Create directory and any missing parent directories
  New-Item -ItemType Directory -Path docs\architecture -Force
  ```
- **POSIX**:
  ```bash
  mkdir -p docs/architecture
  ```

Verify its creation:

```bash
ls docs
```

You should see `architecture` listed under `docs`. 

## 3. Write `TECHNICAL_PASSPORT.md`

Create and populate the `TECHNICAL_PASSPORT.md` file with the content drafted (below). Ensure UTF-8 encoding (no BOM) and LF line endings:

- **PowerShell** (Core 7+ recommended, which uses UTF-8 by default):
  ```powershell
  # Define content as a here-string (@" "@) and write with UTF8 (no BOM) encoding
  @"
# Black Sea Eco Monitor – Technical Project Passport

**Version:** AIR-3.4-complete  
**Tests:** 239 passed  

**Executive Summary:** This document provides a comprehensive technical overview of the Black Sea Eco Monitor project. It includes architecture, libraries, modules, and development guidelines. It is intended for developers new to the project and should be kept up-to-date as the code evolves.

# 1. Project Purpose

- **Name:** Black Sea Eco Monitor  
- **Type:** Web GIS monitoring system for the Black Sea region.  
- **Functionality:** Displays environmental events on a map, including satellite data, atmospheric models, meteorological data, marine drift, evidence panels for events, impact forecasts, and an operator dashboard.

# 2. Overall Architecture

- **Type:** Web-based GIS application (SPA) + Backend API.  
- **Map:** Uses MapLibre GL JS for mapping and spatial layers.  
- **Data Flow:** External data providers (e.g. Sentinel-5P, CAMS, ECMWF, GEOS-CF, EEA) → Backend (FastAPI) → JSON API → Frontend View Models → Renderers → UI/Map.

# 3. Repository Structure

```
black-sea-eco-monitor/
├── backend/        # Python FastAPI backend (data adapters, processing)
├── frontend/       # JavaScript Vite-based frontend application
├── tests/         # Automated tests (frontend and backend)
├── tools/         # Utility scripts and data dumps
├── docs/          # Documentation (architecture, changelog, archive)
│   ├── architecture/
│   ├── changelog/
│   └── archive/
├── README.md      # Project overview and setup
└── LICENSE
```

# 4. Frontend Architecture

- **Technology:** Vanilla JavaScript (no React/Vue). Bundled via Vite.  
- **Entry Point:** `frontend/src/main.js` orchestrates application startup, data loading, and mounting UI components.  
- **Internationalization:** `frontend/src/i18n.js` holds translations (English/Russian). Use `t(lang, key)` to translate; avoid hardcoded strings. **Important:** insert new keys inside `ru:{}` or `en:{}` blocks.  
- **Pipeline:** Data → Normalizers/View Models → Renderers → DOM. Do not render raw API data directly.

# 5. Key Frontend Modules

- **Map:** Uses MapLibre to display GeoJSON layers (via custom map adapters).  
- **Evidence Dashboard (Event Panel):**  
  - **Location:** `frontend/src/evidence/`.  
  - **Structure:** Hook → Mount → Shell (`evidenceDashboardPanel.js`) → Content (`evidencePanelContentMount.js`) → Renderer (`evidencePanelRenderer.js`).  
  - **Sub-components:**  
    - *Incident Summary* (`shareIncidentSummary.js`) – renders summary text, requires `currentLanguage`.  
    - *Timeline* (`evidenceTimelineUX.js`) – vertical timeline of evidence events. **Note:** ensure using the correct renderer; do not confuse with other timeline modules.  
    - *Impact Forecast* (`impactForecastResult.js`) – shows impact data.  
    - *Data Sources Overview* – lists involved data sources.  
    - *UX Cleanup:* remove redundant headers, improve layout and styling.  
- **Weather/Drift/Satellite:** Various modules under `frontend/src/`, each with their own data mappers and renderers.

# 6. Testing

- **Runner:** Node-based test suite (`npm test`).  
- **Status:** 239 tests passing (as of commit `AIR-3.4-complete`).  
- **Location:** Tests mirror module structure, e.g. `frontend/src/...*.test.js`.  
- **Guidelines:** Tests should check contracts and behavior, not hardcoded text (to avoid breaking on localization changes).

# 7. Development Guidelines

- **Commit Messages:** Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (types like `feat:`, `fix:`, `chore:`). Use `chore:` for non-functional tasks (e.g. adding docs).  
- **Localization:** Always use `t(lang, key)`. Verify new keys by calling `t("ru","key")` and `t("en","key")` in a REPL.  
- **New Features:** Find the *actual* renderer and data pipeline before coding UI. Search for function calls (`Select-String render*`) to identify correct modules.  
- **File Encodings:** Save files as UTF-8 (no BOM) with LF endings. In PowerShell 7+, use `-Encoding utf8NoBom` or `Out-File`; in Linux, use `LF` (`\n`) explicitly. For Windows, avoid CRLF in the source files (use ``"`n"`` for newlines in scripts).

# 8. Current Baseline

- **Git Tag:** `AIR-3.4-complete` on branch `main` (up-to-date with `origin/main`).  
- **Tests:** 239 passed, 0 failed.  
- **Note:** This is a clean baseline for further development.

```plaintext
$ git log -3 --oneline
AIR-3.4-complete localization and evidence panel UX cleanup
...
```

🗎 End of Technical Passport
"@ | Out-File -FilePath docs\architecture\TECHNICAL_PASSPORT.md -Encoding utf8NoBOM
  ```
  *Explanation:* We use `Out-File -Encoding utf8NoBOM` to ensure UTF-8 without BOM. Inside PowerShell, ``"`n"`` creates LF line breaks.

- **POSIX (Linux/Mac)**:
  ```bash
  cat << 'EOF' > docs/architecture/TECHNICAL_PASSPORT.md
# Black Sea Eco Monitor – Technical Project Passport

**Version:** AIR-3.4-complete  
**Tests:** 239 passed  

**Executive Summary:** This document provides a comprehensive technical overview of the Black Sea Eco Monitor project. It includes architecture, libraries, modules, and development guidelines. It is intended for developers new to the project and should be kept up-to-date as the code evolves.

# 1. Project Purpose

- **Name:** Black Sea Eco Monitor  
- **Type:** Web GIS monitoring system for the Black Sea region.  
- **Functionality:** Displays environmental events on a map, including satellite data, atmospheric models, meteorological data, marine drift, evidence panels for events, impact forecasts, and an operator dashboard.

# 2. Overall Architecture

- **Type:** Web-based GIS application (SPA) + Backend API.  
- **Map:** Uses MapLibre GL JS for mapping and spatial layers.  
- **Data Flow:** External data providers (e.g. Sentinel-5P, CAMS, ECMWF, GEOS-CF, EEA) → Backend (FastAPI) → JSON API → Frontend View Models → Renderers → UI/Map.

# 3. Repository Structure

\`\`\`
black-sea-eco-monitor/
├── backend/        # Python FastAPI backend (data adapters, processing)
├── frontend/       # JavaScript Vite-based frontend application
├── tests/         # Automated tests (frontend and backend)
├── tools/         # Utility scripts and data dumps
├── docs/          # Documentation (architecture, changelog, archive)
│   ├── architecture/
│   ├── changelog/
│   └── archive/
├── README.md      # Project overview and setup
└── LICENSE
\`\`\`

# 4. Frontend Architecture

- **Technology:** Vanilla JavaScript (no React/Vue). Bundled via Vite.  
- **Entry Point:** \`frontend/src/main.js\` orchestrates application startup, data loading, and mounting UI components.  
- **Internationalization:** \`frontend/src/i18n.js\` holds translations (English/Russian). Use \`t(lang, key)\` to translate; avoid hardcoded strings. **Important:** insert new keys inside \`ru:{ }\` or \`en:{ }\` blocks.  
- **Pipeline:** Data → Normalizers/View Models → Renderers → DOM. Do not render raw API data directly.

# 5. Key Frontend Modules

- **Map:** Uses MapLibre to display GeoJSON layers (via custom map adapters).  
- **Evidence Dashboard (Event Panel):**  
  - **Location:** \`frontend/src/evidence/\`.  
  - **Structure:** Hook → Mount → Shell (\`evidenceDashboardPanel.js\`) → Content (\`evidencePanelContentMount.js\`) → Renderer (\`evidencePanelRenderer.js\`).  
  - **Sub-components:**  
    - *Incident Summary* (\`shareIncidentSummary.js\`) – renders summary text, requires \`currentLanguage\`.  
    - *Timeline* (\`evidenceTimelineUX.js\`) – vertical timeline of evidence events. **Note:** ensure using the correct renderer; do not confuse with other timeline modules.  
    - *Impact Forecast* (\`impactForecastResult.js\`) – shows impact data.  
    - *Data Sources Overview* – lists involved data sources.  
    - *UX Cleanup:* remove redundant headers, improve layout and styling.  
- **Weather/Drift/Satellite:** Various modules under \`frontend/src/\`, each with their own data mappers and renderers.

# 6. Testing

- **Runner:** Node-based test suite (\`npm test\`).  
- **Status:** 239 tests passing (as of commit \`AIR-3.4-complete\`).  
- **Location:** Tests mirror module structure, e.g. \`frontend/src/...*.test.js\`.  
- **Guidelines:** Tests should check contracts and behavior, not hardcoded text (to avoid breaking on localization changes).

# 7. Development Guidelines

- **Commit Messages:** Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (types like \`feat:\`, \`fix:\`, \`chore:\`). Use \`chore:\` for non-functional tasks (e.g. adding docs).  
- **Localization:** Always use \`t(lang, key)\`. Verify new keys by calling \`t("ru","key")\` and \`t("en","key")\` in a REPL.  
- **New Features:** Find the *actual* renderer and data pipeline before coding UI. Search for function calls (e.g. \`Select-String render*\`) to identify correct modules.  
- **File Encodings:** Save files as UTF-8 (no BOM) with LF endings. In PowerShell 7+, use \`-Encoding utf8NoBom\` or \`Out-File\`; in Linux, use LF (`\n`) explicitly. 

# 8. Current Baseline

- **Git Tag:** \`AIR-3.4-complete\` on branch \`main\` (up-to-date with \`origin/main\`).  
- **Tests:** 239 passed, 0 failed.  
- **Note:** This is a clean baseline for further development.

\`\`\`plaintext
$ git log -3 --oneline
AIR-3.4-complete localization and evidence panel UX cleanup
...
\`\`\`

🗎 End of Technical Passport
EOF
  ```

*Explanation:* In POSIX we use `cat << 'EOF' > file` with the content. The single quotes around `EOF` preserve line breaks exactly, and we terminate with `EOF`.

### 3.1 Verify File Encoding and Line Endings

- **PowerShell:** Check file exists and show first/last bytes:
  ```powershell
  # Ensure file exists
  Test-Path docs\architecture\TECHNICAL_PASSPORT.md

  # Optional: display first few bytes (UTF-8 BOM would start with EF BB BF)
  Get-Content docs\architecture\TECHNICAL_PASSPORT.md -Encoding byte -TotalCount 3
  ```
  If UTF-8 without BOM, the bytes should not be EF BB BF. Also check no `\r` characters if inspecting raw content.

- **POSIX:** Check line endings:
  ```bash
  # Show line endings (LF or CRLF)
  od -c docs/architecture/TECHNICAL_PASSPORT.md | head -n 1
  ```
  Lines should end with `\n`, not `\r\n`.

### 3.2 Compute SHA-256 Checksum

After creation, compute SHA-256 to document and verify integrity:

- **PowerShell:**
  ```powershell
  Get-FileHash -Algorithm SHA256 docs\architecture\TECHNICAL_PASSPORT.md
  ```
- **POSIX:**
  ```bash
  sha256sum docs/architecture/TECHNICAL_PASSPORT.md
  ```

*Expected:* A 64-character hex hash is printed. Record it. Example format:
```
e3b0c44298fc1c14...  docs/architecture/TECHNICAL_PASSPORT.md
```

## 4. Stage and Commit

Stage the new file and commit:

- **PowerShell / POSIX:**
  ```bash
  git add docs/architecture/TECHNICAL_PASSPORT.md
  git commit -m "chore: add architecture TECHNICAL_PASSPORT.md"
  ```
*Expected:* One new commit is created. The commit message follows Conventional Commits (type `chore` for adding a documentation file).

Verify with:
```bash
git log -1 --oneline
```
It should show the new commit with message `"chore: add architecture TECHNICAL_PASSPORT.md"`.

## 5. Push to `origin/main`

Before pushing, ensure no one has pushed new commits:

```bash
git fetch
git status
```

- If `git status` indicates your branch is behind `origin/main`, do:
  ```bash
  git pull --rebase
  ```
- If there are uncommitted changes (working tree not clean), either commit or stash them.

Once up-to-date and clean, push:

```bash
git push origin main
```

If your remote has protection (like required reviews), you may create a pull request instead (see step 9 below).

## 6. Verify Remote

Fetch the remote and check that the file exists on `origin/main`:

- Show last commits on `origin/main`:
  ```bash
  git fetch origin
  git log -3 --oneline origin/main
  ```
  You should see your latest commit (`chore: add architecture TECHNICAL_PASSPORT.md`) at the top.

- Show the remote file content:
  ```bash
  git show origin/main:docs/architecture/TECHNICAL_PASSPORT.md
  ```
  This should output the file content (or at least the beginning of it). For a quick check:
  ```bash
  git show origin/main:docs/architecture/TECHNICAL_PASSPORT.md | head -n 5
  ```
  Expected output (first lines):
  ```
  # Black Sea Eco Monitor – Technical Project Passport
  **Version:** AIR-3.4-complete  
  **Tests:** 239 passed
  ```

## 7. Pull Request Template (optional)

If you prefer to use a Pull Request instead of pushing directly, use a brief PR description. For example:

```
### Summary
Add a new technical passport document for architecture overview.

### Changes
- Created `docs/architecture/TECHNICAL_PASSPORT.md` with project overview and guidelines.

### Verification
- File content reviewed.
- `npm test` still passes.

_No code changes - documentation only._
```

## 8. Potential Risks & Rollback

- **Wrong branch:** If not on `main`, pushing could overwrite wrong branch. Always confirm `git branch` first.
- **Uncommitted changes:** If `git status` is not clean, new file could accidentally be left out or conflict. Always commit or stash first.
- **Remote diverged:** If someone pushed to `main` concurrently, your push will be rejected. In that case, fetch and rebase or merge carefully, then push.

**Rollback steps:** If something goes wrong, you can undo the local commit and remote push:

- **Revert locally (before pushing):**  
  ```bash
  git reset HEAD~1  # Undo last commit, keep changes unstaged
  ```
- **Revert after push:**  
  - If you want to “undo” the commit on `main`:  
    ```bash
    git revert HEAD
    git push origin main
    ```  
    This creates a new commit that undoes the changes.  
  - If you must completely erase the commit (not recommended on `main`), you could `git reset --hard HEAD~1` and then force-push:
    ```bash
    git reset --hard HEAD~1
    git push --force-with-lease origin main
    ```
    ⚠️ *Use force-push only if you are absolutely sure no one else has pulled the broken commit, and coordinate with team members.*

In normal practice, it’s safer to use `git revert` to undo a pushed commit on the main branch.

---

**Outcome:** Following these steps will cleanly add the `TECHNICAL_PASSPORT.md` file under `docs/architecture`, with proper encoding and commit history. All changes are trackable and can be verified as described above. This establishes a solid documentation baseline (`AIR-3.4-complete`) for future development.

