import weakref
import re
from gosts import GOSTS


def converting_indexes_to_numbers(indexes: [int], orders: ['Tasks.MultivareTask']):
    """
    Преобразует список индексов заказов в список номеров и ссылок
    :param indexes: список индексов заказов
    :param orders: список заказов элементов класса
    :return: (список номеров заказа, список ссылок на заказы)
    """
    return list(map(lambda i: orders[i], indexes))



