import ctypes
import os

class MatlabNOxModel:

    # Описание модели
    description = (
        'Модель NOx (MATLAB)'
        'Входы: TK, PK, GTG_SAU, TT, PFR_RASH. '
        'Режимы: 0 - стандартный режим'
    )

    input_name = 'TK,PK,GTG_SAU,TT,PFR_RASH'
    output_name = 'NOx'
    io_desc = 'Входные параметры / Выход NOx'
    io_unit = 'ppm'

    def __init__(self, coefs=None):
        # Инициализация модели
        if coefs is None:
            coefs = self._get_default_coefs()
        self.coefs = coefs
        self.dll_path = coefs.get('dll_path', '')
        self.dll = None
        self.is_initialized = False
        self.inputs = None
        self.outputs = None

    def _get_default_coefs(self):
        # Константа по умолчанию, тут это путь к dll
        return {
            'dll_path': 'dll/Model_NOx_v17_win64.dll',  # Относительный путь
        }

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

    def load_data(self):
        # Загрузка DLL и инициализация модели
        import sys
        import os

        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))

        # Проверяем, существует ли DLL по указанному пути
        if not os.path.exists(self.dll_path):
            alt_path = os.path.join(base_path, 'dll', os.path.basename(self.dll_path))
            if os.path.exists(alt_path):
                self.dll_path = alt_path
            else:
                raise FileNotFoundError(f"DLL не найдена: {self.dll_path}")

        # Загрузка DLL
        self.dll = ctypes.CDLL(self.dll_path)
        print(f"DLL загружена: {self.dll_path}")

        # Получение структур из DLL
        try:
            rtU_ptr = self.dll.Model_NOx_v17_U
            rtY_ptr = self.dll.Model_NOx_v17_Y

            class ExtU(ctypes.Structure):
                _fields_ = [
                    ("TK", ctypes.c_double),
                    ("PK", ctypes.c_double),
                    ("GTG_SAU", ctypes.c_double),
                    ("TT", ctypes.c_double),
                    ("PFR_RASH", ctypes.c_double),
                ]

            class ExtY(ctypes.Structure):
                _fields_ = [
                    ("NO", ctypes.c_double),
                ]

            self.inputs = ctypes.cast(rtU_ptr, ctypes.POINTER(ExtU)).contents
            self.outputs = ctypes.cast(rtY_ptr, ctypes.POINTER(ExtY)).contents

        except Exception as e:
            raise RuntimeError(f"Ошибка подключения к структурам DLL: {e}")

        # Получение функций модели
        try:
            self.initialize = self.dll.Model_NOx_v17_initialize
            self.step = self.dll.Model_NOx_v17_step
            self.terminate = self.dll.Model_NOx_v17_terminate

            self.initialize.argtypes = []
            self.initialize.restype = None
            self.step.argtypes = []
            self.step.restype = None
            self.terminate.argtypes = []
            self.terminate.restype = None

        except AttributeError as e:
            raise RuntimeError(f"Ошибка получения функций из DLL: {e}")

        self.initialize()
        self.is_initialized = True


    def calculate(self, x_input):
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        # Устанавливаем входные данные (один раз для всего цикла)
        if isinstance(x_input, dict):
            for name in self.input_names:
                if name in x_input:
                    setattr(self.inputs, name, float(x_input[name]))
        else:
            for i, name in enumerate(self.input_names):
                setattr(self.inputs, name, float(x_input[i]))

        # Важно: 52 шага подряд
        for _ in range(52):
            self.step()  # Один шаг модели

        # Возвращаем результат после 52 шагов
        return self.outputs.NO

    def reset(self):
        # Сброс модели
        if self.is_initialized:
            self.terminate()
            self.initialize()