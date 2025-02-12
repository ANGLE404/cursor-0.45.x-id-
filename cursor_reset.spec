# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cursor45 mail 美化.py'],  # 主程序文件
    pathex=[],
    binaries=[],
    datas=[
        ('locales/*.json', 'locales'),  # 语言文件
        ('logo.py', '.'),  # logo文件
        ('main.py', '.'),  # 主程序
        ('cursor_register.py', '.'),  # 注册程序
        ('reset_machine_manual.py', '.'),  # 重置程序
        ('quit_cursor.py', '.'),  # 退出程序
    ],
    hiddenimports=[
        'PyQt6',
        'win32security',
        'win32api',
        'win32con',
        'psutil',
        'colorama',
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
    name='Cursor Reset',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 添加图标
    uac_admin=True,  # 请求管理员权限
    version='file_version_info.txt',  # 版本信息文件
) 