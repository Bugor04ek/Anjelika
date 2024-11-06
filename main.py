from Tasks import WireDrawingTask, MultivareTask, Order, TaskMeta, OrderMeta
import new_genetika  # Алгоритмы для генетической оптимизации

import pandas as pd


def create_orders():

    file_name = 'excel/Заказы.xlsx'
    excel_data = pd.read_excel(file_name, sheet_name="Лист5")
    excel_data['Дата выпуска по заказу'] = pd.to_datetime(excel_data['Дата выпуска по заказу'],
                                                          format='%d.%m.%Y').dt.date
    data = pd.DataFrame(excel_data).fillna(0)

    return [Order(row) for index, row in data.iterrows()]


def main():
    # Шаг 1: Инициализация заказов
    create_orders()  # создаем заказы, хранятся в OrderMeta

    # Шаг 2: Получаем все заказы с использованием метакласса OrderMeta
    orders = OrderMeta.get_all_instances()
    print(f"Создано {len(orders)} заказов")

    # Шаг 3: Получаем задания из экземпляров Order, например:
    # tasks = [task for order in orders for task in order.task]
    tasks = TaskMeta.get_instances_all()
    print(*tasks, sep='\n')

    # Шаг 4: Запуск генетического алгоритма с выбранными заданиями
    new_genetika.run(tasks)
    print("Генетический алгоритм завершен")


if __name__ == "__main__":
    main()
