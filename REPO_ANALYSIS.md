# EyeYantra Repository — Detailed Analysis

_Generated 2026-07-08. Reflects the state of the `main` branch (HEAD `98ff483`) and the current working tree on this machine._

## 1. What this project is

EyeYantra is a clinical/research tool built for an **IIT Tirupati strabismus (eye-misalignment) research project**. It runs a battery of ocular diagnostic tests — Hirschberg corneal reflex test, a "9-gaze" pattern test, and preliminary intake/eye-detection checks — using a webcam or a custom BLE/Wi-Fi headset ("Ameba" board), processes the captured images with OpenCV/MediaPipe, and generates PDF/text patient reports.

It has three delivery surfaces:
1. **Flask web backend** (`app_api.py`) — the core application logic and UI (server-rendered HTML via `templates/` + `static/`).
2. **Electron desktop wrapper** (`electron_app/`) — packages the Flask backend into a native Windows/Linux desktop app.
3. **Flutter mobile app** (`eyeyantra_flutter/`) — a separate, apparently independent client (not analyzed in depth here).

There's also embedded/firmware code (`WiFi_BLE_INTERFACE/WiFi_BLE_INTERFACE.ino`) for the Bluetooth/Wi-Fi headset hardware the app pairs with.

## 2. Backend (`app_api.py`)

- **2,585 lines**, single-file Flask app — the whole application (routing, camera handling, BLE, report generation) lives here.
- Key responsibilities:
  - **Camera/streaming**: auto-detects available webcams (`/api/cameras`), MJPEG video streaming (`/video_feed`), and can also pull frames from the Ameba headset over Wi-Fi (`/save_manual_ip`, `/get_stream_ip`) — currently hard-pinned to the laptop webcam via `USE_LAPTOP_CAMERA = True` (line 106), i.e. the headset video path is bypassed for now.
  - **BLE**: uses `bleak` to talk to an `AMEBA_BLE_DEV` device over a Nordic UART-style service (UUIDs at lines 63–68), running its own asyncio event loop in a background thread.
  - **Test workflows**: `/preliminary`, `/hirschberg` + `/hirschberg_capture`, `/9gaze` + `/capture_9gaze`, each with a results page and PDF/text/image download routes.
  - **Reporting**: `overallreport.py` / `_report_appendix.py` (ReportLab) generate combined PDF reports (`/generate_overall_report`, `/download_overall_report`).
  - **Admin/config**: `/admin`, `/save_admin_config`, `/api/admin/config`, `/api/admin/patients` — clinic/doctor metadata is stored in `admin_config.json` (clinic name "KIMS", doctor, technician, contact info — this is effectively environment/config data checked into source control, not a secret but worth moving to a template if this repo is ever made public).
  - Processing is delegated to dedicated modules: `results_processing.py`, `HirschbergTest_Processing.py`, `eye_detection.py`, `NineGazeProcessing.py`, `process_nine_gaze_images.py`, `crop_eyes_from_image.py`.
- **Duplicate route definitions**: several routes are defined twice in the file — `/capture` (lines 939 and 999), `/results` (lines 1127, 1166, 1226), and `/capture_9gaze` (lines 1519, 1571). In Flask, the *last* definition wins and silently shadows the earlier one at import time; this is very likely leftover/dead code from iterative edits rather than intentional, and is worth cleaning up since it's a common source of "I changed the route but nothing happened" confusion.
- `sys.stdout`/`print` is monkey-patched at the top of the file (lines 1–20) to avoid `UnicodeEncodeError` crashes on Windows consoles that don't default to UTF-8 — a sign this codebase has already hit Windows console-encoding issues in the field.
- `get_resource_path()` (line 44) handles the PyInstaller-frozen case (`sys._MEIPASS`) so templates/static assets resolve correctly both in dev and inside the packaged `.exe`.

## 3. Desktop wrapper (`electron_app/`)

- `main.js` spawns the backend (prefers a compiled `eye_yantra_backend[.exe]` binary, falls back to `python app_api.py`), shows a loading screen, polls `http://127.0.0.1:5000/` until Flask is up, then loads it in a `BrowserWindow`.
- Cross-platform IPC handlers for **Wi-Fi scan/connect** (`netsh` on Windows, `nmcli` on Linux) and **Bluetooth device auto-selection** (looks for `AMEBA_BLE_DEV`/`EyeYantra` in the device list).
- Kills the backend process on exit (`taskkill /T /F` on Windows, `SIGTERM` on Linux).
- Packaging is via `electron-builder`: NSIS installer + portable `.exe` for Windows, AppImage + `.deb` for Linux (`package.json` → `build` config). Runs `requestedExecutionLevel: requireAdministrator` on Windows (needed for the `netsh`/network-profile calls).

## 4. Windows build pipeline (added in the latest commit)

Commit `98ff483` ("feat: add Windows build support...") introduced:
- `eye_yantra_backend_windows.spec` — PyInstaller spec bundling `app_api.py` + `templates/` + `static/` + MediaPipe's native `modules/` directory into a folder-based `eye_yantra_backend` executable (`console=True`, so a console window stays visible for debugging).
- `build_windows.bat` — a 4-step orchestrator: install Python deps from `requirements_windows.txt` → PyInstaller build → copy the built backend into `electron_app/eye_yantra_backend/` → `npm install && npm run build-win` (electron-builder) inside `electron_app/`.

Toolchain present on this machine: **Python 3.11.15, Node v24.14.1, npm 11.11.0, PyInstaller 6.21.0** — all sufficient to run the pipeline.

## 5. Current working-tree state (important — this will block a build)

`git status` shows a very large diff versus HEAD: roughly **245 deleted, 199 modified, 187 untracked** paths. Two distinct things are going on:

**a) Stale Linux build artifacts under version control.** `electron_app/eye_yantra_backend/` in git contains a *Linux* PyInstaller build (hundreds of `.so` files — `libQt5*.so`, `libavcodec*.so`, a `libpython3.12.so.1.0`, etc.). These were apparently committed from a Linux dev machine. On this Windows checkout they show as deleted/modified because they don't belong here — running the Windows build will regenerate this folder from scratch (`build_windows.bat` step 3 does `rmdir /s /q` + `xcopy` on it), so this is self-healing, but the `.so` files should really never have been committed and will keep causing noisy diffs across platforms until they're removed from tracking (add `electron_app/eye_yantra_backend/` to `.gitignore`).

**b) The actual Electron source files are missing from disk.** `electron_app/main.js`, `package.json`, `preload.js`, `loading.html`, and `README.md` are all tracked and committed in `98ff483`, but are **not present in the working directory** right now — `git status` reports them as deleted. Without these, `npm install && npm run build-win` in step 4 of `build_windows.bat` will fail immediately (no `package.json`). These are recoverable with `git checkout -- electron_app/main.js electron_app/package.json electron_app/preload.js electron_app/loading.html electron_app/README.md` since they're safe/unmodified in git history — nothing has actually been lost, they're just missing locally.

**c) Large volume of generated test-result artifacts.** Most of the remaining deleted/untracked files are per-patient test outputs — `9GazeResults/`, `9gazeRemainingResults/`, `Hirschberg_Results/`, `Preliminary_Results/`, `preliminary/`, `9GazeTestImages/`, `HirschbergTestImages/`, `9GAZEMEDIALTEST/`, `captured_images/` — images (`gaze_*.jpg`, `combined_9gaze.jpg`), grade summaries, and ratio text files, named per patient/session (e.g. `Falsel_2345_12_23_2026_2026-07-01_Areal/`). These look like local clinical-test run output rather than source code, and are almost certainly meant to be gitignored rather than tracked — right now they inflate the repo and produce this kind of noisy `git status` on every session. Worth deciding deliberately whether these should be tracked at all (patient data in a public/shared git history is also a privacy consideration if this repo is ever pushed anywhere non-private).

**d) `my_env/`** — a Python virtualenv (`my_env/bin/python*`, `lib64`) also appears to be partially tracked and is showing as deleted on Windows (it's a Linux venv, so `bin/`, `lib64` won't exist on Windows anyway). Virtualenvs should never be committed; this should be gitignored too.

**e) Untracked files (~187)** — largely new results directories and possibly other work-in-progress files not yet added to git. Not inspected file-by-file here; worth a `git status` review before any `git add -A`.

## 6. Encoding artifact

`requirements_windows.txt` is saved as **UTF-16** (BOM `FF FE` observed), which shows up as literal null-byte-spaced garbage when read as UTF-8 (`a b s l - p y = = 2 . 2 . 0`). Most tools (including `pip install -r`) generally still parse UTF-16 requirements files inconsistently depending on platform/locale — worth re-saving as plain UTF-8 to avoid `pip install -r requirements_windows.txt` failing silently or erroring on some machines.

## 7. Net effect / what's actually blocking "build the Windows .exe" right now

1. Restore the 5 missing `electron_app/*` source files from git (safe, non-destructive — `git checkout --`).
2. Run `build_windows.bat`, which will: reinstall Python deps, rebuild `eye_yantra_backend` with PyInstaller (overwriting the stale Linux artifacts), copy it into `electron_app/`, then run electron-builder to produce `electron_app/dist_installer/EyeYantra Setup*.exe` (installer) and `EyeYantra*.exe` (portable).
3. Longer-term hygiene (not blocking, but worth doing): `.gitignore` the `electron_app/eye_yantra_backend/` build output, `my_env/`, and the per-patient results directories; re-save `requirements_windows.txt` as UTF-8; remove the duplicate Flask route definitions in `app_api.py`.
