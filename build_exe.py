# build_exe.py
import os
import sys
import shutil
import subprocess
import tempfile


def build_exe():
    print("=" * 60)
    print("Полная сборка")
    print("=" * 60)

    # 1. Удаляем старые сборки
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Удалена папка {folder}")

    # 2. Создаем runtime hook
    runtime_hook = '''
# runtime_hook_scipy.py
import sys
import os

if hasattr(sys, '_MEIPASS'):
    scipy_path = os.path.join(sys._MEIPASS, 'scipy')
    if scipy_path not in sys.path:
        sys.path.insert(0, scipy_path)

    import types

    class FakeModule(types.ModuleType):
        def __init__(self, name):
            super().__init__(name)
            self.__path__ = []

        def __getattr__(self, name):
            return None

    sys.modules['scipy._lib.array_api_compat'] = FakeModule('scipy._lib.array_api_compat')
    sys.modules['scipy._lib.array_api_compat.numpy'] = FakeModule('scipy._lib.array_api_compat.numpy')
    sys.modules['scipy._lib.array_api_compat.numpy.fft'] = FakeModule('scipy._lib.array_api_compat.numpy.fft')
    sys.modules['scipy._lib.array_api_compat.numpy.linalg'] = FakeModule('scipy._lib.array_api_compat.numpy.linalg')
    sys.modules['scipy._lib.array_api_compat.common'] = FakeModule('scipy._lib.array_api_compat.common')

    print("Runtime hook активирован")
'''

    hook_file = os.path.join(tempfile.gettempdir(), 'runtime_hook_scipy.py')
    with open(hook_file, 'w', encoding='utf-8') as f:
        f.write(runtime_hook)

    # 3. Команда сборки
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "math_server",

        "--add-data", "dll;dll",
        "--add-data", "math_models;math_models",
        "--add-data", "MathApi_pb2.py;.",
        "--add-data", "MathApi_pb2_grpc.py;.",

        # Скрытые импорты
        "--hidden-import", "ctypes",
        "--hidden-import", "grpc",
        "--hidden-import", "grpc._cython",

        "--runtime-hook", hook_file,
        "--noupx",
        "server.py"
    ]

    print("\nЗапуск сборки...")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='cp866',
        errors='replace'
    )

    if result.returncode == 0:
        print("\nСборка успешна!")

        exe_path = os.path.join("dist", "math_server.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Размер .EXE: {size_mb:.1f} MB")

            print(f"\nФайл: {os.path.abspath(exe_path)}")
        else:
            print(".EXE не создан")
    else:
        print("\nОшибка сборки!")
        if result.stderr:
            print("\nSTDERR")
            print(result.stderr)
        if result.stdout:
            print("\nSTDOUT")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

    # Удаляем временный файл
    if os.path.exists(hook_file):
        os.remove(hook_file)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    build_exe()