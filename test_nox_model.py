import grpc
import MathApi_pb2
import MathApi_pb2_grpc
import time
import uuid


def test_nox_model():
    # Подключение к серверу
    channel = grpc.insecure_channel('localhost:5080')
    stub = MathApi_pb2_grpc.MathApiStub(channel)

    # Получаем список моделей и ищем матлабовскую
    models = stub.GetModels(MathApi_pb2.ArgRequest())
    for m in models.modelNames:
        if 'Модель MATLAB' in m.name:
            model_name = m.name
            break

    if not model_name:
        print("Модель не найдена")
        return

    # Пути к файлам
    dll_path = "D:/Model_NOx_v16_1s50hz_ert_rtw/PracticeModel/Model_NOx_v16_1s50hz_win64.dll"

    # DATA_tabl видимо уже зашит в DLL
    # data_path = "D:/Model_NOx_v16_1s50hz_ert_rtw/PracticeModel/DATA_tabl.mat"

    # Константы
    constants = [
        MathApi_pb2.Constant(name="dll_path", value=dll_path),
        # MathApi_pb2.Constant(name="data_path", value=data_path),
    ]

    # Изначальные параметры
    base_input = {'TK': 800, 'PK': 15, 'GTG_SAU': 100, 'TT': 500, 'PFR_RASH': 2}

    # Тест 1
    print("\nТест 1 - Прогрев модели (60 шагов)")
    model_id = str(uuid.uuid4())
    stub.Start(MathApi_pb2.ArgStart(modelId=model_id, modelName=model_name, constants=constants))

    timestamp = int(time.time() * 1000)

    for step in range(60):
        tags_val = []
        for name, value in base_input.items():
            tag = MathApi_pb2.TagVal(
                tagName=name,
                timeStamp=timestamp + step,
                numericValue=value,
                isGood=True
            )
            tags_val.append(tag)

        transform_req = MathApi_pb2.ArgData(
            modelId=model_id,
            tagsVal=tags_val
        )

        # Отправка на сервер и получение результата, в ответе массив tagsVal с выходным тегом
        response = stub.Transform(transform_req)
        nox = response.tagsVal[0].numericValue if response.tagsVal else 0

        print(
            f"Шаг {step + 1}\tTK={base_input['TK']}\tPK={base_input['PK']}\tGTG={base_input['GTG_SAU']}\tTT={base_input['TT']}\tPFR_RASH={base_input['PFR_RASH']}\tNOx={nox:.2f}")

    stub.Stop(MathApi_pb2.ArgModel(modelId=model_id))

    # Тест 2 - TK
    print("\nТест 2: TK (от 750 до 950)")
    model_id = str(uuid.uuid4())
    stub.Start(MathApi_pb2.ArgStart(modelId=model_id, modelName=model_name, constants=constants))

    tk_values = [750, 780, 800, 820, 850, 870, 900, 920, 950]

    for i, tk in enumerate(tk_values):
        test_input = base_input.copy()
        test_input['TK'] = tk

        tags_val = []
        for name, value in test_input.items():
            tag = MathApi_pb2.TagVal(
                tagName=name,
                timeStamp=timestamp + 100 + i,
                numericValue=value,
                isGood=True
            )
            tags_val.append(tag)

        transform_req = MathApi_pb2.ArgData(
            modelId=model_id,
            tagsVal=tags_val
        )

        response = stub.Transform(transform_req)
        nox = response.tagsVal[0].numericValue if response.tagsVal else 0

        print(
            f"Шаг {i + 1}\tTK={test_input['TK']}\tPK={test_input['PK']}\tGTG={test_input['GTG_SAU']}\tTT={test_input['TT']}\tPFR_RASH={base_input['PFR_RASH']}\tNOx={nox:.2f}")

    stub.Stop(MathApi_pb2.ArgModel(modelId=model_id))

    # Тест 3 - Изменение PK
    print("\nТест 3: PK (от 12 до 20)")
    model_id = str(uuid.uuid4())
    stub.Start(MathApi_pb2.ArgStart(modelId=model_id, modelName=model_name, constants=constants))

    pk_values = [12, 13, 14, 15, 16, 17, 18, 19, 20]

    for i, pk in enumerate(pk_values):
        test_input = base_input.copy()
        test_input['PK'] = pk

        tags_val = []
        for name, value in test_input.items():
            tag = MathApi_pb2.TagVal(
                tagName=name,
                timeStamp=timestamp + 200 + i,
                numericValue=value,
                isGood=True
            )
            tags_val.append(tag)

        transform_req = MathApi_pb2.ArgData(
            modelId=model_id,
            tagsVal=tags_val
        )

        response = stub.Transform(transform_req)
        nox = response.tagsVal[0].numericValue if response.tagsVal else 0

        print(
            f"Шаг {i + 1}\tTK={test_input['TK']}\tPK={test_input['PK']}\tGTG={test_input['GTG_SAU']}\tTT={test_input['TT']}\tPFR_RASH={base_input['PFR_RASH']}\tNOx={nox:.2f}")

    stub.Stop(MathApi_pb2.ArgModel(modelId=model_id))

    # Тест 4 - Изменение GTG
    print("\nТест 4: GTG (от 70 до 130)")
    model_id = str(uuid.uuid4())
    stub.Start(MathApi_pb2.ArgStart(modelId=model_id, modelName=model_name, constants=constants))

    gtg_values = [70, 80, 90, 100, 110, 120, 130]

    for i, gtg in enumerate(gtg_values):
        test_input = base_input.copy()
        test_input['GTG_SAU'] = gtg

        tags_val = []
        for name, value in test_input.items():
            tag = MathApi_pb2.TagVal(
                tagName=name,
                timeStamp=timestamp + 300 + i,
                numericValue=value,
                isGood=True
            )
            tags_val.append(tag)

        transform_req = MathApi_pb2.ArgData(
            modelId=model_id,
            tagsVal=tags_val
        )

        response = stub.Transform(transform_req)
        nox = response.tagsVal[0].numericValue if response.tagsVal else 0

        print(
            f"Шаг {i + 1}\tTK={test_input['TK']}\tPK={test_input['PK']}\tGTG={test_input['GTG_SAU']}\tTT={test_input['TT']}\tPFR_RASH={base_input['PFR_RASH']}\tNOx={nox:.2f}")

    stub.Stop(MathApi_pb2.ArgModel(modelId=model_id))


if __name__ == "__main__":
    test_nox_model()