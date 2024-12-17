import time
from fastapi import FastAPI
from pydantic import BaseModel
import json
import random


from datetime import datetime
from typing import TextIO

from Equipments import initialize_equipments, MultivareMachine, Equipment
from Tasks import Order, TaskMeta, OrderMeta, Task, WireDrawingMachine, WireDrawingTask, MultivareTask

import new_genetika  # Алгоритмы для генетической оптимизации


equipments = None
app = FastAPI()

# Модель данных
class JsonArray(BaseModel):
    data: list


def create_orders():

    file_name = 'excel/Заказы.json'

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
    # file_name = 'excel/Заказы.xlsx'
    # excel_data = pd.read_excel(file_name, sheet_name="Лист5")
    # excel_data['Дата выпуска по заказу'] = pd.to_datetime(
    #     excel_data['Дата выпуска по заказу'],
    #     format='%d.%m.%Y'
    #     ).dt.date
    # data = pd.DataFrame(excel_data).fillna(0)
    #
    # return [Order(row) for index, row in data.iterrows()]


def main():
    # Шаг 0: Заведение оборудований
    equipments = initialize_equipments()

    # Шаг 1: Инициализация заказов
    create_orders()  # создаем заказы, хранятся в OrderMeta

    # Шаг 2: Получаем все заказы с использованием метакласса OrderMeta
    orders = OrderMeta.get_all_instances()

    # Шаг 4: Запуск генетического алгоритма с выбранными заданиями

    time_begin = datetime.now()
    best_orders = new_genetika.run()
    time_end = datetime.now()

    total_time = time_end - time_begin
    print(total_time)

    result_json = {}
    for eq in Equipment.get_all_instances():
        for equipment_type in eq.equipment_type:
            if result_json.get(equipment_type, None) is None:
                result_json[equipment_type] = {}
            result_json[equipment_type][eq.equipment_name] = [{"UUID": task.order.UUID,"Маршрут": task.spin_road, "Комментарий": task.comment_setup} for task in best_orders.get(equipment_type, {}).get(eq.equipment_name, [])]
            # result_json.append({"UUID": task.order.UUID,"Маршрут": task.spin_road, "Комментарий": task.comment_setup} for task in best_orders.get(equipment_type, {}).get(eq.equipment_name, []))


    print("Генетический алгоритм завершен")

    return result_json

# эндпоинт для перемешивания JSON
@app.post("/shuffle_json")
def shuffle_json(payload: JsonArray):

    # Путь к файлу
    file_name = 'excel/Заказы.json'

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

