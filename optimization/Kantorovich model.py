import pulp
import numpy as np
import itertools as it
from dataclasses import dataclass
from collections import Counter

@dataclass
class Data:
    """Исходные данные для модели."""
    # Максимальная ширина исходных рулонов.
    BOBBIN_SIZE = 32.365
    # Количество заказов в штуках каждого типа рулонов.
    orders = [9, 79, 90, 27]
    # Ширина заказов каждого типа. Соответствие по индексу в списке.
    # Так необходимо 9 рулонов ширины 3, 79 рулонов ширины 5 и т.д.
    order_sizes = [3, 5, 6, 9]
    # Список паттернов, по каким может быть нарезан исходный рулон.
    # Так, например, паттерн [1, 0, 1, 0] означает, что из исходного рулона ширины 10,
    # может быть вырезан рулон ширины 3 и рулон ширины 6.
    patterns = [[0, 0, 0, 1],
                [0, 0, 1, 0],
                [1, 0, 1, 0],
                  [0, 1, 0, 0],
                [0, 2, 0, 0],
                [1, 1, 0, 0],
                [1, 0, 0, 0],
                [2, 0, 0, 0],
                [3, 0, 0, 0]]
    # Общее количество заказов.
    RAWS_NUMBER = sum(orders)

#  Инициализация модели.
model = pulp.LpProblem('Kantorovich model', pulp.LpMinimize)

# Задание типа переменных (возможность указать их не только целочисленными неоходима
# для оценки целевой функции линейной релаксации).
#vars_type = pulp.LpContinuous
vars_type = pulp.LpInteger

# Создание необходимых индексов для переменных, для каждого исходного рулона.
cuts_ids = range(data.RAWS_NUMBER)
# Создание переменных, соответствующих y_{k}.
cuts = pulp.LpVariable.dicts("raw_cut", cuts_ids, lowBound=0, upBound=1, cat=vars_type)