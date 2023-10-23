import pandas as pd
import scipy
import consts
import CreateTable


def target_function():
    pass


def counting_spinners(table):
    """
    Выгружаем значения диаметров из основной таблицы. Находим в словаре фильер ближайшие значения к диаметру.
    Добавляем 2 столбца в основную таблицу
    :param table: главная таблица с основными параметрами
    """
    # массивы для диаметров из таблицы
    d, d_plus = [], []
    # временные массивы для фильер
    temp_spin, temp_spin_plus = [], []

    for row in table.rows:
        d.append(row[5])
        d_plus.append(row[6])

    for num in d:
        # Расшифровка строки ниже:
        #  1. это лямбда-функция, которая принимает ключ словаря "key" (диаметр) и возвращает абсолютное значение
        #  разницы между этим ключом и "num" (диаметр из таблицы).
        #  2. min() - это встроенная функция Python, которая принимает итерируемый объект (в данном случае, словарь) и
        #  ключ (функцию), который используется для вычисления значения,
        #  на основе которого будет производиться сравнение элементов
        #  3. min() возвращает элемент словаря с наименьшей разницей между ключами и забираем его из словаря через []
        #  4. Добавляем полученное значение во временный массив
        temp_spin.append(consts.dictionary_spinners[min(consts.dictionary_spinners, key=lambda x: abs(num - x))])

    for num in d_plus:
        # если диаметр 0, значит кабель не плюсовой, значит 0 фильер
        if num != 0:
            # описание смотри выше
            temp_spin_plus.append(consts.dictionary_spinners[min(consts.dictionary_spinners, key=lambda x: abs(num - x))])
        else:
            temp_spin_plus.append(0)

    table.add_column("Количество фильер", temp_spin)
    table.add_column("Количество фильер +", temp_spin_plus)


if __name__ == '__main__':
    info_table = CreateTable.create_tables()
    counting_spinners(info_table)
    print(info_table)


