# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for the desktop build.

Build with: python -m PyInstaller RogueFPS.spec --noconfirm
Output:     dist/RogueFPS/RogueFPS.exe (copy the whole folder to distribute)
"""
from pathlib import Path

ROOT = Path(SPECPATH)
RUNTIME = ROOT / 'Assets/Art/pixel_portal_v1/runtime'
SOURCE = ROOT / 'Assets/Art/pixel_portal_v1/source'
AUDIO = ROOT / 'Assets/audio'

datas = [
    (str(RUNTIME), 'Assets/Art/pixel_portal_v1/runtime'),
    (str(AUDIO), 'Assets/audio'),
]
for name in ('melee_v5_sword.png', 'melee_v7_spear.png', 'melee_v7_sword.png'):
    datas.append((str(SOURCE / name), 'Assets/Art/pixel_portal_v1/source'))

a = Analysis(
    ['fps_game.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name='RogueFPS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'RogueFPS.ico'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RogueFPS',
)