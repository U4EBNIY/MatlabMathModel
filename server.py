import grpc
from concurrent import futures
import traceback
import sys
import os

# Импорт protobuf файлов
import MathApi_pb2
import MathApi_pb2_grpc

# Импорт MATLAB модели
from math_models.matlab_nox import MatlabNOxModel


class ModelManager:
    # Класс для управления моделями

    def __init__(self):
        self.models = {}

    def create_model(self, model_id, model_name, constants):
        # Создание новой модели
        if model_id in self.models:
            self.remove_model(model_id)

        # Проверка, что запрашиваемая модель существует
        if model_name != "Модель MATLAB":
            return False, f"Модель '{model_name}' не найдена"

        try:
            # Преобразуем константы в словарь
            const_dict = {const.name: const.value for const in constants}

            # Создаем экземпляр модели
            model = MatlabNOxModel(const_dict)
            # Загружаем данные (DLL)
            model.load_data()

            # Сохраняем в словаре
            self.models[model_id] = {
                'instance': model,
                'name': model_name,
                'constants': const_dict
            }

            print(f"Модель создана: {model_name} (id: {model_id})")
            return True, "Модель успешно создана"
        except FileNotFoundError as e:
            return False, f"Ошибка: {str(e)}"
        except Exception as e:
            traceback.print_exc()
            return False, f"Ошибка: {str(e)}"

    def get_model(self, model_id):
        # Получить модель по ID
        return self.models.get(model_id)

    def remove_model(self, model_id):
        # Удалить модель по ID
        if model_id in self.models:
            # Вызываем reset для сброса состояния
            try:
                self.models[model_id]['instance'].reset()
            except:
                pass
            del self.models[model_id]
            print(f"Модель удалена: {model_id}")
            return True
        return False

    def calculate(self, model_id, input_dict):
        # Вычислить результат с помощью модели
        model_data = self.get_model(model_id)
        if not model_data:
            return None

        model = model_data['instance']

        try:
            result = model.calculate(input_dict)
            return result
        except Exception as e:
            traceback.print_exc()
            return None


class MathApi(MathApi_pb2_grpc.MathApiServicer):
    # Основной класс gRPC сервера

    def __init__(self):
        self.model_manager = ModelManager()

    def GetModels(self, request, context):
        # Получить список доступных моделей
        try:
            model = MatlabNOxModel()
            items = [MathApi_pb2.ModelName(
                name="Модель MATLAB",
                desc=model.description
            )]
            return MathApi_pb2.Models(modelNames=items)
        except Exception as e:
            return MathApi_pb2.Models(message=f"Err_{str(e)}")

    def GetConstants(self, request, context):
        # Получить константы для указанной модели
        try:
            if request.modelName != "Модель MATLAB":
                return MathApi_pb2.Constants(message="Err_Модель не найдена")

            model = MatlabNOxModel()
            constants = []
            for name, value in model._get_default_coefs().items():
                constants.append(MathApi_pb2.Constant(name=name, value=str(value)))
            return MathApi_pb2.Constants(constantValues=constants)
        except Exception as e:
            return MathApi_pb2.Constants(message=f"Err_{str(e)}")

    def GetInputTags(self, request, context):
        # Получить описание входных тегов
        try:
            if request.modelName != "Модель MATLAB":
                return MathApi_pb2.Tags(message="Err_Модель не найдена")

            model = MatlabNOxModel()
            tags = []
            for name in model.input_names:
                tags.append(MathApi_pb2.TagType(
                    name=name,
                    desc=f"Входной параметр {name}",
                    unit=model.io_units
                ))
            return MathApi_pb2.Tags(tags=tags)
        except Exception as e:
            return MathApi_pb2.Tags(message=f"Err_{str(e)}")

    def GetOutputTags(self, request, context):
        # Получить описание выходных тегов
        try:
            if request.modelName != "Модель MATLAB":
                return MathApi_pb2.Tags(message="Err_Модель не найдена")

            model = MatlabNOxModel()
            tags = [MathApi_pb2.TagType(
                name="Y",
                desc="Выход NOx",
                unit=model.io_units
            )]
            return MathApi_pb2.Tags(tags=tags)
        except Exception as e:
            return MathApi_pb2.Tags(message=f"Err_{str(e)}")

    def Start(self, request, context):
        # Запуск модели
        try:
            model_id = request.modelId
            model_name = request.modelName
            constants = request.constants

            print(f"Start: {model_name} (id: {model_id})")

            success, message = self.model_manager.create_model(
                model_id, model_name, constants
            )

            if success:
                return MathApi_pb2.RetReply(message="Start успешен")
            else:
                return MathApi_pb2.RetReply(message=f"Err_{message}")
        except Exception as e:
            return MathApi_pb2.RetReply(message=f"Err_{str(e)}")

    def Transform(self, request, context):
        # Шаг вычисления
        try:
            model_id = request.modelId
            print(f"Transform для модели {model_id}")

            # Преобразуем входные теги в словарь
            input_dict = {}
            for tag in request.tagsVal:
                input_dict[tag.tagName] = tag.numericValue

            print(f"Входные данные: {input_dict}")

            # Вычисляем результат
            result = self.model_manager.calculate(model_id, input_dict)

            if result is not None:
                timestamp = request.tagsVal[-1].timeStamp if request.tagsVal else 0
                response = MathApi_pb2.TagsDataArray()
                response.tagsVal.append(MathApi_pb2.TagVal(
                    tagName="Y",
                    timeStamp=timestamp,
                    numericValue=float(result),
                    isGood=True
                ))
                print(f"Результат: Y={result}")
                return response
            else:
                return MathApi_pb2.TagsDataArray(message="Err_Ошибка вычисления")
        except Exception as e:
            print(f"Ошибка Transform: {e}")
            traceback.print_exc()
            return MathApi_pb2.TagsDataArray(message=f"Err_{str(e)}")

    def Stop(self, request, context):
        # Остановка модели
        try:
            model_id = request.modelId
            print(f"Stop: {model_id}")
            success = self.model_manager.remove_model(model_id)
            if success:
                return MathApi_pb2.RetReply(message="Stop успешен")
            else:
                return MathApi_pb2.RetReply(message="Err_Модель не найдена")
        except Exception as e:
            return MathApi_pb2.RetReply(message=f"Err_{str(e)}")

    def Pause(self, request, context):
        # Пауза (не используется, но метод должен быть)
        print(f"Pause: {request.modelId}")
        return MathApi_pb2.RetReply(message="Pause успешен")


def serve():
    # Функция запуска gRPC сервера
    port = "5080"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Добавление сервиса к серверу
    MathApi_pb2_grpc.add_MathApiServicer_to_server(MathApi(), server)

    # Настройка порта
    server.add_insecure_port("[::]:" + port)

    # Вывод информации о запуске
    print(f"Сервер запущен на порту {port}")
    print("Доступные модели: Модель MATLAB (только NOx)")
    print("Ожидание подключений...")

    # Запуск сервера
    server.start()
    # Ожидание завершения работы
    server.wait_for_termination()


if __name__ == "__main__":
    serve()