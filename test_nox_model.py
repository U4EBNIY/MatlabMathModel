import grpc
import MathApi_pb2
import MathApi_pb2_grpc
import time
import uuid
import random


def test_nox_model_v17():
    channel = grpc.insecure_channel('localhost:5080')
    stub = MathApi_pb2_grpc.MathApiStub(channel)

    # Получаем список моделей
    models = stub.GetModels(MathApi_pb2.ArgRequest())
    for m in models.modelNames:
        if 'Модель MATLAB' in m.name:
            model_name = m.name
            break

    if not model_name:
        print("Модель не найдена")
        return

    # Путь к DLL
    dll_path = "D:/Model_NOx_v16_1s50hz_ert_rtw/PracticeModel/Model_NOx_v17_win64.dll"
    constants = [MathApi_pb2.Constant(name="dll_path", value=dll_path)]

    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ NOx")
    print("=" * 80)

    # Запуск модели
    print("\n1. ЗАПУСК МОДЕЛИ")
    model_id = str(uuid.uuid4())
    response = stub.Start(MathApi_pb2.ArgStart(modelId=model_id, modelName=model_name, constants=constants))
    print(f"   Start response: {response.message}")

    if "успешен" not in response.message:
        print("   Модель не запустилась")
        return

    timestamp = int(time.time() * 1000)
    STEPS_PER_SLICE = 52

    # ПРОГРЕВ
    print("\n2. ПРОГРЕВ МОДЕЛИ")
    print("-" * 60)

    tags_val = []
    base_time = timestamp

    for step in range(STEPS_PER_SLICE):
        tags_val.append(MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=800.0, isGood=True))
        tags_val.append(MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=15.0, isGood=True))
        tags_val.append(
            MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=100.0, isGood=True))
        tags_val.append(MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=500.0, isGood=True))
        tags_val.append(
            MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=2.0, isGood=True))

    response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
    print(f"   Прогрев: TK:800 PK:15 GTG:100 TT:500 PFR:2.0 === NOx = {response.tagsVal[0].numericValue:.2f}")

    # ТЕСТ 1: ТЕМПЕРАТУРА
    print("\n" + "=" * 80)
    print("ТЕСТ 1: ИЗМЕНЕНИЕ ТЕМПЕРАТУРЫ (TK)")
    print("=" * 80)

    temperatures = [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100]

    for i, tk in enumerate(temperatures):
        tags_val = []
        base_time = timestamp + 100000 + i * 100000

        for step in range(STEPS_PER_SLICE):
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=float(tk), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=15.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=100.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=500.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=2.0, isGood=True))

        response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
        print(f"TK:{tk} PK:15 GTG:100 TT:500 PFR:2.0 === NOx = {response.tagsVal[0].numericValue:.2f}")

    # ТЕСТ 2: ДАВЛЕНИЕ
    print("\n" + "=" * 80)
    print("ТЕСТ 2: ИЗМЕНЕНИЕ ДАВЛЕНИЯ (PK)")
    print("=" * 80)

    pressures = [5, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

    for i, pk in enumerate(pressures):
        tags_val = []
        base_time = timestamp + 2000000 + i * 100000

        for step in range(STEPS_PER_SLICE):
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=800.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=float(pk), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=100.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=500.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=2.0, isGood=True))

        response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
        print(f"TK:800 PK:{pk} GTG:100 TT:500 PFR:2.0 === NOx = {response.tagsVal[0].numericValue:.2f}")

    # ТЕСТ 3: РАСХОД
    print("\n" + "=" * 80)
    print("ТЕСТ 3: ИЗМЕНЕНИЕ РАСХОДА (GTG)")
    print("=" * 80)

    flows = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]

    for i, gtg in enumerate(flows):
        tags_val = []
        base_time = timestamp + 4000000 + i * 100000

        for step in range(STEPS_PER_SLICE):
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=800.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=15.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=float(gtg), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=500.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=2.0, isGood=True))

        response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
        print(f"TK:800 PK:15 GTG:{gtg} TT:500 PFR:2.0 === NOx = {response.tagsVal[0].numericValue:.2f}")

    # ТЕСТ 4: ТЕМПЕРАТУРА ТОПЛИВА
    print("\n" + "=" * 80)
    print("ТЕСТ 4: ИЗМЕНЕНИЕ ТЕМПЕРАТУРЫ ТОПЛИВА (TT)")
    print("=" * 80)

    fuel_temps = [300, 350, 400, 450, 500, 550, 600, 650, 700]

    for i, tt in enumerate(fuel_temps):
        tags_val = []
        base_time = timestamp + 6000000 + i * 100000

        for step in range(STEPS_PER_SLICE):
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=800.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=15.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=100.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=float(tt), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=2.0, isGood=True))

        response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
        print(f"TK:800 PK:15 GTG:100 TT:{tt} PFR:2.0 === NOx = {response.tagsVal[0].numericValue:.2f}")

    # ТЕСТ 5: PFR
    print("\n" + "=" * 80)
    print("ТЕСТ 5: ИЗМЕНЕНИЕ PFR_RASH")
    print("=" * 80)

    pfr_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    for i, pfr in enumerate(pfr_values):
        tags_val = []
        base_time = timestamp + 8000000 + i * 100000

        for step in range(STEPS_PER_SLICE):
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=800.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=15.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=100.0, isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=500.0, isGood=True))
            tags_val.append(MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=float(pfr),
                                               isGood=True))

        response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
        print(f"TK:800 PK:15 GTG:100 TT:500 PFR:{pfr} === NOx = {response.tagsVal[0].numericValue:.2f}")

    # ТЕСТ 6: ВСЁ РАНДОМНО
    print("\n" + "=" * 80)
    print("ТЕСТ 6: ВСЕ ПАРАМЕТРЫ РАНДОМНО")
    print("=" * 80)

    random.seed(42)

    for i in range(10):
        tk = random.randint(600, 1100)
        pk = random.randint(8, 30)
        gtg = random.randint(40, 150)
        tt = random.randint(350, 600)
        pfr = round(random.uniform(0.8, 3.5), 1)

        tags_val = []
        base_time = timestamp + 10000000 + i * 100000

        for step in range(STEPS_PER_SLICE):
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TK", timeStamp=base_time + step, numericValue=float(tk), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="PK", timeStamp=base_time + step, numericValue=float(pk), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="GTG_SAU", timeStamp=base_time + step, numericValue=float(gtg), isGood=True))
            tags_val.append(
                MathApi_pb2.TagVal(tagName="TT", timeStamp=base_time + step, numericValue=float(tt), isGood=True))
            tags_val.append(MathApi_pb2.TagVal(tagName="PFR_RASH", timeStamp=base_time + step, numericValue=float(pfr),
                                               isGood=True))

        response = stub.Transform(MathApi_pb2.ArgData(modelId=model_id, tagsVal=tags_val))
        print(f"TK:{tk} PK:{pk} GTG:{gtg} TT:{tt} PFR:{pfr} === NOx = {response.tagsVal[0].numericValue:.2f}")

    stub.Stop(MathApi_pb2.ArgModel(modelId=model_id))
    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)


if __name__ == "__main__":
    test_nox_model_v17()