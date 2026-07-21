# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ('core', 'core'),
    ('frontend/qml/QmlProbe.qml', 'frontend/qml'),
    ('frontend/qml/TopBar.qml', 'frontend/qml'),
    ('frontend/qml/ThemePopup.qml', 'frontend/qml'),
    ('frontend/qml/PlayerCard.qml', 'frontend/qml'),
    ('frontend/qml/PlayerCardRow.qml', 'frontend/qml'),
    ('frontend/qml/PlayerCardPrototype.qml', 'frontend/qml'),
]
datas += collect_data_files('qtawesome')


a = Analysis(
    ['frontend\\QApplication.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['aiohappyeyeballs', 'aiohttp', 'aiosignal', 'asyncio', 'attrs', 'certifi', 'charset_normalizer', 'cryptography', 'cryptography.hazmat.primitives.serialization.pkcs12', 'frozenlist', 'idna', 'msgspec', 'multidict', 'PIL', 'propcache', 'PySide6', 'PySide6_Addons', 'PySide6_Essentials', 'qasync', 'qtawesome', 'requests', 'shiboken6', 'superqt', 'urllib3', 'yarl', 'websockets', 'xml.etree.ElementTree', 'aiofiles'],
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
    a.binaries,
    a.datas,
    [],
    name='ValScanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\logoone.ico'],
)
