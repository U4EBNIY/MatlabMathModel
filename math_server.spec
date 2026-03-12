# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[('dll', 'dll'), ('math_models', 'math_models'), ('MathApi_pb2.py', '.'), ('MathApi_pb2_grpc.py', '.')],
    hiddenimports=['ctypes', 'grpc', 'grpc._cython'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['C:\\Users\\Techn\\AppData\\Local\\Temp\\runtime_hook_scipy.py'],
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
    name='math_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
