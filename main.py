import Tasks  # Базовые константы и параметры для Order и Task
from Equipments import WireDrawingMachine, MultivareMachine
from Tasks import WireDrawingTask, MultivareTask
import new_genetika  # Алгоритмы для генетической оптимизации

import pandas as pd


def create_orders():

    file_name = 'excel/Заказы.xlsx'
    excel_data = pd.read_excel(file_name, sheet_name="Лист5")
    excel_data['Дата выпуска по заказу'] = pd.to_datetime(excel_data['Дата выпуска по заказу'],
                                                          format='%d.%m.%Y').dt.date
    data = pd.DataFrame(excel_data).fillna(0)

    return [Tasks.Order(row) for index, row in data.iterrows()]


def main():
    # Начальная инициализация, создание экземпляров и задание параметров
    orders = create_orders()  # функция для создания всех заказов
    tasks = []
    for order in orders:
        # Инициализация заданий для каждого заказа
        if 'WireDrawing' in order.operation_sequence:
            tasks.append(WireDrawingTask(order))
        if 'Multivare' in order.operation_sequence:
            tasks.append(MultivareTask(order))

    # Запуск генетического алгоритма для распределения заданий
    new_genetika.run(tasks)


if __name__ == "__main__":
    main()