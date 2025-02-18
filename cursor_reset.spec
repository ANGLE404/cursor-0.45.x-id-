# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct

block_cipher = None

# 定义图标文件名
ICON_FILE = 'Hacker_News_icon-icons.com_55898.ico'

# 定义源文件名 - 使用实际的文件名
SOURCE_FILE = 'cursor45mail.py'

# 定义VIP激活脚本
VIP_SCRIPT = 'cursor_pro_keep_alive.py'

# 定义所有需要的数据文件
potential_datas = [
    (ICON_FILE, '.'),  # 图标文件
    ('config.ini', '.'),  # 配置文件
    (VIP_SCRIPT, '.'),  # VIP激活脚本
    ('cursor_auth_manager.py', '.'),
    ('browser_utils.py', '.'),
    ('get_email_code.py', '.'),
    ('logo.py', '.'),
    ('logger.py', '.')
]

# 过滤出存在的文件
datas = [(src, dst) for src, dst in potential_datas if os.path.exists(src)]

# 主程序分析
a = Analysis(
    [SOURCE_FILE],  # 主程序源文件
    pathex=[],
    binaries=[],
    datas=datas,  # 所有数据文件
    hiddenimports=[
        'win32security',
        'win32api', 
        'win32con',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'ntsecuritycon',
        'ctypes',
        'json',
        'uuid',
        'shutil',
        'logging',
        'subprocess',
        'winreg',
        'colorama',
        'DrissionPage'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# VIP激活脚本分析
b = Analysis(
    [VIP_SCRIPT],  # VIP激活脚本源文件
    pathex=[],
    binaries=[],
    datas=datas,  # 使用相同的数据文件
    hiddenimports=[
        'colorama',
        'DrissionPage',
        'json',
        'uuid',
        'logging'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# 主程序PYZ
pyz_a = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# VIP激活脚本PYZ
pyz_b = PYZ(
    b.pure,
    b.zipped_data,
    cipher=block_cipher
)

# 主程序EXE
exe_a = EXE(
    pyz_a,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Cursor重置工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_FILE if os.path.exists(ICON_FILE) else None,
    uac_admin=True,
    version_info=VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=(1, 0, 0, 0),
            prodvers=(1, 0, 0, 0),
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0)
        ),
        kids=[
            StringFileInfo([
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'CompanyName', u'AYC404'),
                        StringStruct(u'FileDescription', u'Cursor重置工具'),
                        StringStruct(u'FileVersion', u'1.0.0'),
                        StringStruct(u'InternalName', u'cursor_reset'),
                        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 AYC404'),
                        StringStruct(u'OriginalFilename', u'Cursor重置工具.exe'),
                        StringStruct(u'ProductName', u'Cursor重置工具'),
                        StringStruct(u'ProductVersion', u'1.0.0')
                    ]
                )
            ]),
            VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
        ]
    )
)

# VIP激活脚本EXE
exe_b = EXE(
    pyz_b,
    b.scripts,
    b.binaries,
    b.zipfiles,
    b.datas,
    [],
    name='CursorPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # VIP激活脚本使用控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_FILE if os.path.exists(ICON_FILE) else None,
    uac_admin=True
)

# 将两个EXE打包在一起
COLLECT(
    exe_a,
    exe_b,
    a.binaries,
    a.zipfiles,
    a.datas,
    b.binaries,
    b.zipfiles,
    b.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cursor工具集'
) 