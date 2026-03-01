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

    # Инициализация
    def __init__(self, coefs=None):
        if coefs is None:
            coefs = self._get_default_coefs()
        self.coefs = coefs
        self.dll_path = coefs.get('dll_path', '')
        # self.data_path = coefs.get('data_path', '')
        self.dll = None
        self.is_initialized = False
        self.inputs = None
        self.outputs = None
        self._warmup_steps = 0

    def _get_default_coefs(self):
        # Константы по умолчанию
        return {
            'dll_path': 'D:/Model_NOx_v16_1s50hz_ert_rtw/PracticeModel/Model_NOx_v16_1s50hz_win64.dll',
            # 'data_path': 'D:/Model_NOx_v16_1s50hz_ert_rtw/PracticeModel/DATA_tabl.mat'
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

    # Загрузка данных, вызывается 1 раз
    def load_data(self):
        if not os.path.exists(self.dll_path):
            raise FileNotFoundError(f"DLL не найдена: {self.dll_path}")

        # Загрузка DLL
        self.dll = ctypes.CDLL(self.dll_path)
        print(f"DLL загружена: {self.dll_path}")

        # Получение структур из DLL через ctypes
        try:
            rtU_ptr = self.dll.Model_NOx_v16_1s50hz_U
            rtY_ptr = self.dll.Model_NOx_v16_1s50hz_Y

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

        self.initialize()
        self.is_initialized = True

    # Вызывается на каждом шаге расчёта
    def calculate(self, x_input):
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        # Установка входных данных
        if isinstance(x_input, dict):
            for name in self.input_names:
                if name in x_input:
                    setattr(self.inputs, name, float(x_input[name]))
        else:
            if len(x_input) != 5:
                raise ValueError(f"Ожидается 5 параметров, получено {len(x_input)}")
            self.inputs.TK = float(x_input[0])
            self.inputs.PK = float(x_input[1])
            self.inputs.GTG_SAU = float(x_input[2])
            self.inputs.TT = float(x_input[3])
            self.inputs.PFR_RASH = float(x_input[4])

        # Вызов шага расчёта
        self.step()
        self._warmup_steps += 1

        # Возврат результата
        return self.outputs.NO

    # Сброс модели
    def reset(self):
        if self.is_initialized:
            self.terminate()
            self.initialize()
            self._warmup_steps = 0