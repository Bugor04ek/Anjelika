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
    d = []
    # временные массивы для фильер
    temp_spin = []

    for row in table.rows:
        d.append(row[6])

    for num in d:
        # Расшифровка строки ниже:
        #  1. это лямбда-функция, которая принимает ключ словаря "key" (диаметр) и возвращает абсолютное значение
        #  разницы между этим ключом и "num" (диаметр из таблицы).
        #  2. min() - это встроенная функция Python, принимающая итерируемый объект (в данном случае, словарь) и
        #  ключ (функцию), используемый для вычисления значения,
        #  на основе которого будет производиться сравнение элементов
        #  3. min() возвращает элемент словаря с наименьшей разницей между ключами и забираем его из словаря через []
        #  4. Добавляем полученное значение во временный массив
        temp_spin.append(consts.dictionary_spinners[min(consts.dictionary_spinners, key=lambda x: abs(num - x))])

    # Здесь был плюсовой, мб потом что-то доработаем

    table.add_column("Количество фильер", temp_spin)


if __name__ == '__main__':
    info_table = CreateTable.create_tables()
    counting_spinners(info_table)
    print(info_table)


