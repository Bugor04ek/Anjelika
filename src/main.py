from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import sys
import os
import threading


from datetime import datetime
from typing import TextIO

from src.Equipments import initialize_equipments, Equipment
from Tasks import Order, OrderMeta, Basket, TaskMeta

import new_genetika  # Алгоритмы для генетической оптимизации


equipments = None
app = FastAPI()

# Модель данных
class JsonArray(BaseModel):
    data: list


def create_orders():

    file_name = 'data/Заказы.json'

    with open(file_name, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    orders = []
    for item in json_data:
        if 'ВремяНаВолочение' not in item:
            continue

        # Преобразование даты в формат datetime.date, если требуется
        if 'ДатаВыпускаПоЗаказу' in item and item['ДатаВыпускаПоЗаказу']:
            item['ДатаВыпускаПоЗаказу'] = datetime.strptime(item['ДатаВыпускаПоЗаказу'], '%d.%m.%Y %H:%M:%S').date()

        # Создаем экземпляр Order для каждого заказа
        orders.append(Order(item))

    return orders


def main():
    # Шаг 0: Заведение оборудований
    equipments = initialize_equipments()

    # Шаг 1: Инициализация заказов
    create_orders()  # создаем заказы, хранятся в OrderMeta

    # Шаг 2: Получаем все заказы с использованием метакласса OrderMeta
    orders = OrderMeta.get_all_instances()

    # Шаг 4: Запуск генетического алгоритма с выбранными заданиями

    # time_begin = datetime.now()
    best_orders = new_genetika.run()
    # time_end = datetime.now()

    # total_time = time_end - time_begin
    # print(total_time)

    result_json = {}
    for eq in Equipment.get_all_instances():
        for equipment_type in eq.equipment_type:
            if result_json.get(equipment_type, None) is None:
                result_json[equipment_type] = {}

            for task in best_orders.get(equipment_type, {}).get(eq.equipment_name, []):
                f = 1
                pass



            result_json[equipment_type][eq.equipment_name] = [
                # Для НЕ корзин
                {"ЭтоКорзина": False,
                 "UUID": task.order.UUID,
                 "Маршрут": task.spin_road,
                 "Комментарий": task.comment_setup,
                 "Штраф": task.time_penalty,
                 "ВремяВРаботе": task.time_work,
                 "ВремяПеренастройки": task.time_setup}
                if not isinstance(task, Basket) else
                # Для корзин
                {"ЭтоКорзина": True,
                 "Штраф": task.time_penalty,
                 "Маршрут": task.spin_road,
                 "Диаметр": task.diameter,
                 "ВремяВРаботе": task.time_work,
                 "ВремяЗаказовДоКорзины": task.total_time,
                 "ПервыйЗаказНаКорзине": task.orders[0].order.UUID,
                 "ПослединийЗаказНаКорзине": task.orders[-1].order.UUID}
                for task in best_orders.get(equipment_type, {}).get(eq.equipment_name, [])
            ]

            # result_json[equipment_type][eq.equipment_name] = [{"Штраф": task.time_penalty, "Маршрут": task.spin_road, "ВремяВРаботе": task.time_work} for task in best_orders.get(equipment_type, {}).get(eq.equipment_name, [])]

        # result_json.append({"UUID": task.order.UUID,"Маршрут": task.spin_road, "Комментарий": task.comment_setup} for task in best_orders.get(equipment_type, {}).get(eq.equipment_name, []))

    print("Генетический алгоритм завершен")

    return result_json

# эндпоинт для вызова ошибки и выхода из проги
@app.post("/reload")
def shutdown():
    # Запуск функции с задержкой 5 секунд
    threading.Timer(1, delayed_function).start()

    # Возвращаем ответ
    return JSONResponse(content={"message": "Приложение будет перезапущено через 1 секунду."})


def delayed_function():
    # Перезапускаем приложение
    print("Приложение должно быть перезапущено после этого сообщения.")
    python = sys.executable  # Путь к интерпретатору Python
    os.execl(python, python, *sys.argv)  # Заменяем текущий процесс новым




# эндпоинт для замены длины корзины в JSON
@app.post("/calculate_basket")
def calculate_basket(payload: JsonArray):

    #Посчитать остаток корзин
    # Путь к файлам заказов и мультика
    file_name_for_orders = 'data/Заказы.json'
    file_name_for_new_basket_length = 'data/Multivare.json'

    # try:

    # Получаем JSON из запроса
    json_data = payload.model_dump()

    # Записываем JSON в файл
    with open(file_name_for_orders, 'w', encoding='utf-8') as json_file:  # type: TextIO
        json.dump(json_data['data'], json_file, ensure_ascii=False, indent=4)

    equipments = initialize_equipments()
    create_orders()  # создаем заказы, хранятся в OrderMeta
    orders = OrderMeta.get_all_instances()
    # Генерация начальной популяции
    inds = new_genetika.generate_population(TaskMeta.get_instances_all(), 1)
    baskets = new_genetika.calculating_basket(inds[0], True)

    # try:
    remaining_basket_length = max(0.1, round((8 - (baskets[-1].sum_basket)),2))
    # except:
        # print(len(orders))
        # print(len(inds))
        # print(len(inds[0]['multivare']))
        # print(len(baskets))


    with open(file_name_for_new_basket_length, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Обновляем значение поля remaining_basket_length
    data["multivare"]["remaining_basket_length"] = remaining_basket_length

    with open(file_name_for_new_basket_length, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Возвращаем данные обратно клиенту
    return {"status": remaining_basket_length}

    # #Если не получилось обработать запрос
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}

# эндпоинт для перемешивания JSON
@app.post("/shuffle_json")
def shuffle_json(payload: JsonArray):
    # Путь к файлу
    file_name = 'data/Заказы.json'

    # Получаем JSON из запроса
    json_data = payload.model_dump()

    # Записываем JSON в файл
    with open(file_name, 'w', encoding='utf-8') as json_file:  # type: TextIO
        json.dump(json_data['data'], json_file, ensure_ascii=False, indent=4)

    # Возвращаем перемешанный массив
    return {"Order": main()}



if __name__ == "__main__":
    result_json = main()

    print(result_json)