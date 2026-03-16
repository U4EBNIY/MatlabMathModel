import grpc
from concurrent import futures
import traceback
import configparser
import sys
import os

import MathApi_pb2
import MathApi_pb2_grpc

from math_models.matlab_nox import MatlabNOxModel


class ModelManager:

    # Менеджер для создания, хранения и удаления экземпляров моделей
    def __init__(self):
        self.models = {}

    def create_model(self, model_id, model_name, constants):
        if model_id in self.models:
            self.remove_model(model_id)

        # Проверяем, что запрос на нужную модель
        if model_name != "Модель MATLAB":
            return False, f"Модель '{model_name}' не найдена"

        try:

            # Преобразуем константы из списка в словарь
            const_dict = {const.name: const.value for const in constants}

            # Создаем экземпляр модели
            model = MatlabNOxModel(const_dict)
            model.load_data()
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

        # Возвращает данные модели по ID или None, если модели нет
    def get_model(self, model_id):
        return self.models.get(model_id)

        # Удаляет модель по ID
    def remove_model(self, model_id):
        if model_id in self.models:
            try:
                self.models[model_id]['instance'].reset()
            except:
                pass
            del self.models[model_id]
            print(f"Модель удалена: {model_id}")
            return True
        return False


class MathApi(MathApi_pb2_grpc.MathApiServicer):

    # gRPC-сервис MathApi
    def __init__(self):
        self.model_manager = ModelManager()

    # Возвращает список доступных моделей
    def GetModels(self, request, context):
        try:
            model = MatlabNOxModel()
            items = [MathApi_pb2.ModelName(
                name="Модель MATLAB",
                desc=model.description
            )]
            return MathApi_pb2.Models(modelNames=items)
        except Exception as e:
            return MathApi_pb2.Models(message=f"Err_{str(e)}")

    # Возвращает список констант модели
    def GetConstants(self, request, context):
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

    # Возвращает описание входных тегов модели
    def GetInputTags(self, request, context):
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

    # Возвращает описание выходных тегов модели
    def GetOutputTags(self, request, context):
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

    # Запускает модель
    def Start(self, request, context):
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

        # Основной метод расчета
        # Получает пакет данных (много тегов), разбивает на отдельные наборы,
        # считает результат для каждого набора и возвращает все результаты
        try:
            model_id = request.modelId
            model_data = self.model_manager.get_model(model_id)
            if not model_data:
                return MathApi_pb2.TagsDataArray(message="Err_Модель не найдена")

            model = model_data['instance']
            all_tags = list(request.tagsVal)

            if not all_tags:
                return MathApi_pb2.TagsDataArray(message="Err_Нет входных данных")

            # Определяем количество наборов данных (5 тегов на набор)
            num_sets = len(all_tags) // 5
            print(f"\n{'=' * 60}")
            print(f"Transform: {len(all_tags)} тегов, {num_sets} наборов данных")
            print(f"{'=' * 60}")

            # Группируем теги по именам параметров (TK, PK, GTG_SAU, TT, PFR_RASH)
            tag_dict = {}
            for tag in all_tags:
                if tag.tagName not in tag_dict:
                    tag_dict[tag.tagName] = []
                tag_dict[tag.tagName].append(tag)

            # Проверяем наличие всех обязательных параметров
            required_params = ['TK', 'PK', 'GTG_SAU', 'TT', 'PFR_RASH']
            for param in required_params:
                if param not in tag_dict:
                    return MathApi_pb2.TagsDataArray(message=f"Err_Отсутствует параметр {param}")

            # Собираем наборы данных по шагам
            datasets = []
            for set_idx in range(num_sets):
                dataset = {}
                for param in required_params:
                    tag = tag_dict[param][set_idx]
                    dataset[param] = tag.numericValue
                datasets.append(dataset)

            # Вычисляем результаты и собираем их в один ответ
            response = MathApi_pb2.TagsDataArray()
            print(f"\nРезультаты:")
            print(f"{'-' * 60}")

            for idx, dataset in enumerate(datasets):
                try:
                    result = model.calculate(dataset)

                    # Добавляем каждый результат как отдельный тег Y
                    response.tagsVal.append(MathApi_pb2.TagVal(
                        tagName="Y",
                        timeStamp=tag_dict['TK'][idx].timeStamp,
                        numericValue=float(result),
                        isGood=True
                    ))

                    print(f"  Набор {idx + 1:2d}: ", end="")
                    print(f"TK={dataset['TK']:6.1f}, ", end="")
                    print(f"PK={dataset['PK']:6.2f}, ", end="")
                    print(f"GTG={dataset['GTG_SAU']:6.1f}, ", end="")
                    print(f"TT={dataset['TT']:6.1f}, ", end="")
                    print(f"PFR={dataset['PFR_RASH']:4.2f}  ->  ", end="")
                    print(f"NOx = {result:8.2f}")

                except Exception as e:
                    print(f"  Ошибка на наборе {idx + 1}: {e}")

                    # В случае ошибки добавляем 0 с флагом isGood=False
                    response.tagsVal.append(MathApi_pb2.TagVal(
                        tagName="Y",
                        timeStamp=tag_dict['TK'][idx].timeStamp,
                        numericValue=0.0,
                        isGood=False
                    ))

            print(f"{'-' * 60}")
            print(f"Всего результатов: {len(response.tagsVal)}")
            print(f"Последний результат: {response.tagsVal[-1].numericValue:.2f}")
            print(f"{'=' * 60}\n")

            return response

        except Exception as e:
            print(f"Ошибка Transform: {e}")
            traceback.print_exc()
            return MathApi_pb2.TagsDataArray(message=f"Err_{str(e)}")

    def Stop(self, request, context):
        # Останавливает и удаляет модель
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
        # Пауза
        print(f"Pause: {request.modelId}")
        return MathApi_pb2.RetReply(message="Pause успешен")


def serve():
    # Запуск gRPC сервера
    # Читаем конфиг
    config = configparser.ConfigParser()
    config.read('config.ini')

    host = config['server']['host']
    port = config['server']['port']

    # Создаем сервер
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Регистрируем сервис
    MathApi_pb2_grpc.add_MathApiServicer_to_server(MathApi(), server)

    # Запускаем прослушивание на указанном ip и порту
    server.add_insecure_port(f"{host}:{port}")

    print(f"Сервер запущен на {host}:{port}")
    print(f"Для подключения используйте: {host if host != '0.0.0.0' else 'localhost'}:{port}")
    print("Доступные модели: Модель MATLAB (NOx)")
    print("Ожидание подключений...")

    # Запускаем сервер
    server.start()

    # Блокируем основной поток до завершения сервера
    server.wait_for_termination()

if __name__ == "__main__":
    serve()