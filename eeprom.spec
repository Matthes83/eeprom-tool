# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller-Spec fuer das 24C EEPROM Tool.
Erzeugt auf Windows eine .exe, auf macOS eine .app.
Aufruf:  pyinstaller eeprom.spec
"""
import sys

block_cipher = None

a = Analysis(
    ['eeprom_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'serial',
        'serial.tools.list_ports',
        'serial.tools.list_ports_common',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EEPROM-Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI, kein Terminalfenster
    disable_windowed_traceback=False,
    argv_emulation=True,    # macOS: Datei-Drop / Doppelklick sauber
    target_arch=None,       # macOS: None = aktuelle Arch; 'universal2' fuer beide
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# macOS-spezifisch: .app-Bundle erzeugen
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='EEPROM-Tool.app',
        icon=None,
        bundle_identifier='de.local.eeprom-tool',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
