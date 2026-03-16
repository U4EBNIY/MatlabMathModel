import ctypes
import os
import sys


class MatlabNOxModel:
    description = (
        'Модель NOx (MATLAB) '
        'Входы: TK, PK, GTG_SAU, TT, PFR_RASH'
    )

    # Поля Infra Analytics для отображения в интерфейсе
    input_name = 'TK,PK,GTG_SAU,TT,PFR_RASH'
    output_name = 'NOx'
    io_desc = 'Входные параметры / Выход NOx'
    io_unit = 'ppm'

    # Инициализация модели
    # coefs - словарь с константами из Infra Analytics
    def __init__(self, coefs=None):
        if coefs is None:
            coefs = self._get_default_coefs()
        self.coefs = coefs
        self.dll_path = coefs.get('dll_path', '')
        self.dll = None
        self.is_initialized = False
        self.inputs = None
        self.outputs = None

    # Константы по умолчанию
    def _get_default_coefs(self):
        return {
            'dll_path': 'dll/Model_NOx_v16_1s50hz_win64_1.dll',
        }

    # Свойства для Infra Analytics
    @property
    def model_desc(self):
        return self.description

    @property
    def io_descr(self):
        return self.io_desc

    @property
    def io_units(self):
        return self.io_unit

    @property
    def output(self):
        return self.output_name

    @property
    def input(self):
        return self.input_name

    @property
    def input_names(self):
        return ['TK', 'PK', 'GTG_SAU', 'TT', 'PFR_RASH']

        # Загрузка DLL и инициализация модели
        # Вызывается один раз при старте модели
    def load_data(self):
        import sys
        import os

        # Базовый путь для PyInstaller (если запуск через .exe)
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))

        # Проверяем, есть ли DLL по указанному пути
        if not os.path.exists(self.dll_path):
            # Если нет, то dll ищется в папке dll рядом с .exe
            alt_path = os.path.join(base_path, 'dll', os.path.basename(self.dll_path))
            if os.path.exists(alt_path):
                self.dll_path = alt_path
            else:
                raise FileNotFoundError(f"DLL не найдена: {self.dll_path}")

        # Загружаем DLL в память
        self.dll = ctypes.CDLL(self.dll_path)
        print(f"DLL загружена: {self.dll_path}")

        # Получаем указатели на структуры входов и выходов из DLL
        try:
            rtU_ptr = self.dll.Model_NOx_v16_1s50hz_U
            rtY_ptr = self.dll.Model_NOx_v16_1s50hz_Y

            # Описание структуры входных данных (5 полей типа double)
            class ExtU(ctypes.Structure):
                _fields_ = [
                    ("TK", ctypes.c_double),
                    ("PK", ctypes.c_double),
                    ("GTG_SAU", ctypes.c_double),
                    ("TT", ctypes.c_double),
                    ("PFR_RASH", ctypes.c_double),
                ]

            # Описание структуры выходных данных (1 поле типа double)
            class ExtY(ctypes.Structure):
                _fields_ = [
                    ("NO", ctypes.c_double),
                ]

            # Преобразование указателей в Python-объекты
            self.inputs = ctypes.cast(rtU_ptr, ctypes.POINTER(ExtU)).contents
            self.outputs = ctypes.cast(rtY_ptr, ctypes.POINTER(ExtY)).contents

        except Exception as e:
            raise RuntimeError(f"Ошибка подключения к структурам DLL: {e}")

        # Получаем функции из DLL
        try:
            self.initialize = self.dll.Model_NOx_v16_1s50hz_initialize
            self.step = self.dll.Model_NOx_v16_1s50hz_step
            self.terminate = self.dll.Model_NOx_v16_1s50hz_terminate

            self.initialize.argtypes = []
            self.initialize.restype = None
            self.step.argtypes = []
            self.step.restype = None
            self.terminate.argtypes = []
            self.terminate.restype = None

        except AttributeError as e:
            raise RuntimeError(f"Ошибка получения функций из DLL: {e}")

        # Инициализируем модель
        self.initialize()
        self.is_initialized = True

    def calculate(self, x_input):
        # Принимает один набор данных
        # Делает для него 52 шага
        # Возвращает один результат (значение на 52-м шаге)
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        # Приводим данные к словарю
        if not isinstance(x_input, dict):
            x_input = {
                'TK': float(x_input[0]),
                'PK': float(x_input[1]),
                'GTG_SAU': float(x_input[2]),
                'TT': float(x_input[3]),
                'PFR_RASH': float(x_input[4]),
            }

        # Копируем данные из словаря в структуру DLL
        for name in self.input_names:
            if name in x_input:
                setattr(self.inputs, name, float(x_input[name]))

        # 52 шага расчёта для этого набора
        for _ in range(52):
            self.step()

        # Возвращаем результат после 52 шагов
        return self.outputs.NO

    def reset(self):
        if self.is_initialized:
            self.terminate()
            self.initialize()