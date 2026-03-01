# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[('math_models', 'math_models'), ('utils', 'utils'), ('test_data', 'test_data'), ('MathApi_pb2.py', '.'), ('MathApi_pb2_grpc.py', '.')],
    hiddenimports=['scipy', 'scipy.interpolate', 'scipy.interpolate._bspl', 'scipy.interpolate._fitpack', 'scipy.interpolate._ppoly', 'scipy.interpolate.interpnd', 'scipy._lib', 'scipy._lib._ccallback', 'scipy._lib._testutils', 'scipy._lib.array_api_compat', 'scipy._lib.array_api_compat.numpy', 'scipy._lib.array_api_compat.numpy.fft', 'scipy._lib.array_api_compat.numpy.linalg', 'scipy._lib.array_api_compat.common', 'scipy.special', 'scipy.special._ufuncs_cxx', 'scipy.special._specfun', 'platformdirs', 'jaraco.collections', 'jaraco.text', 'jaraco.functools', 'jaraco.context', 'pkg_resources', 'setuptools', 'math_models', 'math_models.interpolation_1d', 'math_models.interpolation_2d', 'math_models.approximation_1d', 'math_models.approximation_2d', 'utils', 'utils.excel_reader', 'grpc', 'grpc._cython', 'pandas', 'openpyxl', 'numpy', 'numpy.core._methods', 'numpy.lib.format'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['C:\\Users\\Mad\\AppData\\Local\\Temp\\runtime_hook_scipy.py'],
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
