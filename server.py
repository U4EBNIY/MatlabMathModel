import grpc
from concurrent import futures
import traceback
import sys
import os

import MathApi_pb2
import MathApi_pb2_grpc

from math_models.matlab_nox import MatlabNOxModel


class ModelManager:

    def __init__(self):
        self.models = {}

    def create_model(self, model_id, model_name, constants):
        if model_id in self.models:
            self.remove_model(model_id)

        if model_name != "Модель MATLAB":
            return False, f"Модель '{model_name}' не найдена"

        try:
            const_dict = {const.name: const.value for const in constants}
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

    def get_model(self, model_id):
        return self.models.get(model_id)

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

    def __init__(self):
        self.model_manager = ModelManager()

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
        try:
            model_id = request.modelId
            model_data = self.model_manager.get_model(model_id)
            if not model_data:
                return MathApi_pb2.TagsDataArray(message="Err_Модель не найдена")

            model = model_data['instance']
            all_tags = list(request.tagsVal)

            if not all_tags:
                return MathApi_pb2.TagsDataArray(message="Err_Нет входных данных")

            # Определяем количество шагов (тегов на параметр)
            steps = len(all_tags) // 5
            print(f"\n{'=' * 60}")
            print(f"Transform: {len(all_tags)} тегов, {steps} раз посчитано")
            print(f"{'=' * 60}")

            # Группируем теги по именам
            tag_dict = {}
            for tag in all_tags:
                if tag.tagName not in tag_dict:
                    tag_dict[tag.tagName] = []
                tag_dict[tag.tagName].append(tag)

            # Проверяем, что есть все 5 параметров
            required = ['TK', 'PK', 'GTG_SAU', 'TT', 'PFR_RASH']
            for req in required:
                if req not in tag_dict:
                    return MathApi_pb2.TagsDataArray(message=f"Err_Нет параметра {req}")

            # Собираем наборы по шагам
            datasets = []
            timestamp = 0
            for step in range(steps):
                dataset = {}
                for param in required:
                    tag = tag_dict[param][step]
                    dataset[param] = tag.numericValue
                    if step == steps - 1:
                        timestamp = tag.timeStamp
                datasets.append(dataset)

            print(f"Собрано {len(datasets)} наборов данных")

            all_results = []
            print(f"\nРезультаты для каждого набора данных:")
            print(f"{'-' * 60}")

            for idx, dataset in enumerate(datasets):
                try:
                    result = model.calculate(dataset)
                    all_results.append(result)
                    print(f"  Набор {idx + 1:2d}: ", end="")
                    print(f"TK={dataset['TK']:6.1f}, ", end="")
                    print(f"PK={dataset['PK']:6.2f}, ", end="")
                    print(f"GTG={dataset['GTG_SAU']:6.1f}, ", end="")
                    print(f"TT={dataset['TT']:6.1f}, ", end="")
                    print(f"PFR={dataset['PFR_RASH']:4.2f}  ->  ", end="")
                    print(f"NOx = {result:8.2f}")
                except Exception as e:
                    print(f"  Ошибка на наборе {idx + 1}: {e}")
                    all_results.append(0.0)

            print(f"{'-' * 60}")
            print(f"Всего получено результатов: {len(all_results)}")
            print(f"Последний результат: {all_results[-1]:.2f}")
            print(f"{'=' * 60}\n")

            if all_results:
                response = MathApi_pb2.TagsDataArray()
                response.tagsVal.append(MathApi_pb2.TagVal(
                    tagName="Y",
                    timeStamp=timestamp,
                    numericValue=float(all_results[-1]),
                    isGood=True
                ))
                return response
            else:
                return MathApi_pb2.TagsDataArray(message="Err_Нет результатов")

        except Exception as e:
            print(f"Ошибка Transform: {e}")
            traceback.print_exc()
            return MathApi_pb2.TagsDataArray(message=f"Err_{str(e)}")

    def Stop(self, request, context):
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
        print(f"Pause: {request.modelId}")
        return MathApi_pb2.RetReply(message="Pause успешен")


def serve():
    port = "5080"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    MathApi_pb2_grpc.add_MathApiServicer_to_server(MathApi(), server)
    server.add_insecure_port("[::]:" + port)

    print(f"Сервер запущен на порту {port}")
    print("Доступные модели: Модель MATLAB (NOx)")
    print("Ожидание подключений...")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()