# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cursor45 mail 美化.py'],
    pathex=[],
    binaries=[],
    datas=[('locales/*.json', 'locales'), ('main.py', '.'), ('cursor_register.py', '.'), ('reset_machine_manual.py', '.'), ('quit_cursor.py', '.'), ('logo.py', '.')],
    hiddenimports=['PyQt6', 'win32security', 'win32api', 'win32con', 'psutil', 'colorama'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Cursor Reset',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='file_version_info.txt',
    uac_admin=True,
    icon=['C:\\Users\\QQB\\CODE\\cursor-reset-main\\cursor-free-vip\\Hacker_News_icon-icons.com_55898.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cursor Reset',
)
