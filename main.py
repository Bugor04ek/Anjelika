import json
from datetime import datetime

from Equipments import initialize_equipments, MultivareMachine
from Tasks import Order, TaskMeta, OrderMeta, Task, WireDrawingMachine
import new_genetika  # Алгоритмы для генетической оптимизации

import pandas as pd


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
    print(f"Создано {len(orders)} заказов")

    # Шаг 3: Получаем задания из экземпляров Order, например:
    # tasks = [task for order in orders for task in order.task]
    tasks_drawing = TaskMeta.get_instances_by_type('wiredrawing')
    tasks_multivare = TaskMeta.get_instances_by_type('multivare')
    # print(*tasks_draggers, sep='\n')

    # Task.assign_tasks_to_equipment(tasks_drawing, available_equipments=WireDrawingMachine.get_all_instances('wiredrawing'))
    # Task.assign_tasks_to_equipment(tasks_multivare, available_equipments=MultivareMachine.get_all_instances('multivare'))
    # print(TaskMeta.get_instances_by_type('wiredrawing'))
    # # print(TaskMeta.get_instances_by_type('multivare'))
    # Шаг 4: Запуск генетического алгоритма с выбранными заданиями
    new_genetika.run(Task.get_instances_all())
    print("Генетический алгоритм завершен")


if __name__ == "__main__":
    main()
