# -*- mode: python ; coding: utf-8 -*-
# EyeYantra Backend - Windows PyInstaller Spec
# Run from the EYE_YENTRA_Code directory:
#   pyinstaller eye_yantra_backend_windows.spec --noconfirm

import sys
import os
from pathlib import Path

# Locate mediapipe modules inside the active venv/site-packages
def find_mediapipe_modules():
    try:
        import mediapipe
        mp_path = Path(mediapipe.__file__).parent / 'modules'
        if mp_path.exists():
            return str(mp_path)
    except ImportError:
        pass
    # Fallback: search common venv locations
    for candidate in ['venv', 'my_env', '.venv']:
        p = Path(candidate) / 'Lib' / 'site-packages' / 'mediapipe' / 'modules'
        if p.exists():
            return str(p)
    return None

mp_modules = find_mediapipe_modules()

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]

if mp_modules:
    datas.append((mp_modules, 'mediapipe/modules'))

a = Analysis(
    ['app_api.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'bleak',
        'cv2',
        'numpy',
        'mediapipe',
        'PIL',
        'reportlab',
        'results_processing',
        'HirschbergTest_Processing',
        'eye_detection',
        'NineGazeProcessing',
        'process_nine_gaze_images',
        'overallreport',
        'crop_eyes_from_image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='eye_yantra_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,           # Keep console visible for debugging; set False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add path to .ico file here if desired e.g. 'electron_app/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eye_yantra_backend',
)
