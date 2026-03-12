import ctypes
import os
import sys


class MatlabNOxModel:
    """
    Модель расчета NOx.
    Принимает ОДИН набор данных, делает 52 шага, возвращает ОДИН результат.
    """

    description = (
        'Модель NOx (MATLAB) '
        'Входы: TK, PK, GTG_SAU, TT, PFR_RASH. '
        'Режимы: 0 - стандартный режим'
    )

    input_name = 'TK,PK,GTG_SAU,TT,PFR_RASH'
    output_name = 'NOx'
    io_desc = 'Входные параметры / Выход NOx'
    io_unit = 'ppm'

    def __init__(self, coefs=None):
        if coefs is None:
            coefs = self._get_default_coefs()
        self.coefs = coefs
        self.dll_path = coefs.get('dll_path', '')
        self.dll = None
        self.is_initialized = False
        self.inputs = None
        self.outputs = None

    def _get_default_coefs(self):
        return {
            'dll_path': 'dll/Model_NOx_v17_win64_1.dll',
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
        import sys
        import os

        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))

        if not os.path.exists(self.dll_path):
            alt_path = os.path.join(base_path, 'dll', os.path.basename(self.dll_path))
            if os.path.exists(alt_path):
                self.dll_path = alt_path
            else:
                raise FileNotFoundError(f"DLL не найдена: {self.dll_path}")

        self.dll = ctypes.CDLL(self.dll_path)
        print(f"DLL загружена: {self.dll_path}")

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
        # Принимает ОДИН набор данных.
        # Делает для него 52 шага.
        # Возвращает ОДИН результат (значение на 52-м шаге).
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        if not isinstance(x_input, dict):
            x_input = {
                'TK': float(x_input[0]),
                'PK': float(x_input[1]),
                'GTG_SAU': float(x_input[2]),
                'TT': float(x_input[3]),
                'PFR_RASH': float(x_input[4]),
            }

        for name in self.input_names:
            if name in x_input:
                setattr(self.inputs, name, float(x_input[name]))

        for _ in range(52):
            self.step()

        return self.outputs.NO

    def reset(self):
        if self.is_initialized:
            self.terminate()
            self.initialize()