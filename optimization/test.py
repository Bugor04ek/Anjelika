from ortools.linear_solver import pywraplp
from scipy.optimize import minimize
from consts import *
from Multik import *


def create_data_model(orders, container_capacity):
    """Create the data for the example."""
    data = {}
    data["orders"] = orders
    data["items"] = list(range(len(orders)))
    data["bins"] = data["items"]
    data["bin_capacity"] = container_capacity
    return data


def create_solution(orders: list[TaskForMultik], container_capacity: float, release_date: object) -> object:
    data = create_data_model(orders, container_capacity)

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")

    if not solver:
        return

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    x = {}
    for i in data["items"]:
        for j in data["bins"]:
            x[(i, j)] = solver.IntVar(0, 1, "x_%i_%i" % (i, j))

    # y[j] = 1 if bin j is used.
    y = {}
    for j in data["bins"]:
        y[j] = solver.IntVar(0, 1, "y[%i]" % j)

    # Constraints
    # Each item must be in exactly one bin.
    for i in data["items"]:
        solver.Add(sum(x[i, j] for j in data["bins"]) == 1)

    # The amount packed in each bin cannot exceed its capacity.
    for j in data["bins"]:
        solver.Add(
            sum(x[(i, j)] * data["orders"][i].full_bobbin[1] for i in data["items"])
            <= y[j] * data["bin_capacity"]
        )

    for j in data["bins"]:
        solver.Add(
            sum(x[(i, j)] * data["orders"][i].full_bobbin[2] for i in data["items"])
            <= y[j] * 2
        )

    # Objective: minimize the number of bins used.
    solver.Minimize(solver.Sum([y[j] for j in data["bins"]]))

    status = solver.Solve()
    result = {"orders": [], }
    num_bins = 0
    if status == pywraplp.Solver.OPTIMAL:
        for j in data["bins"]:
            if y[j].solution_value() == 1:
                bin_orders = []
                orders = []
                bin_length = 0
                bin_dates = []
                bobbin = Bobbin(0, data["bin_capacity"], release_date, None)
                check_list_multik.append(bobbin)
                for i in data["bins"]:
                    if x[i, j].solution_value() > 0:
                        bin_orders.append(data["orders"][i].account_number)
                        bobbin.add(data["orders"][i].full_bobbin[1], data["orders"][i])
                        orders.append(data["orders"][i].account_number)
                        bin_length += data["orders"][i].full_bobbin[1]  # Используем длину кабеля на неполной катушке
                        bin_dates.append(data["orders"][i].order.release_date)
                if bin_orders:
                    num_bins += 1
                    print("Bin number", j)
                    print("  Orders packed:", bin_orders)
                    print("  Total length:", bin_length)
                    print("  Release dates:", bin_dates)
                    print()
        print()
        print("Number of bins used:", num_bins)
        print("Time = ", solver.WallTime(), " milliseconds")
    else:
        print("The problem does not have an optimal solution.")

    return num_bins


def objective_function(params, *args):
    # Параметры оптимизации: диаметр и количество проволок
    diameter, wire_count = params
    # Вычисление суммарного времени настройки
    total_setup_time = calculate_total_setup_time(args[0])

    # Вычисление суммарного штрафа за просрочку заказов
    # total_penalty = calculate_total_penalty(orders)

    # Целевая функция: минимизация суммарного времени настройки и штрафа
    return total_setup_time  # + total_penalty


# Функция для вычисления суммарного времени настройки
def calculate_total_setup_time(orders: list[TaskForMultik]):
    total_setup_time = 0
    previous_order = None

    for order in orders:
        if previous_order is not None:
            # Вычисляем разницу между предыдущим и текущим заказами

            """
                1 ПРОВЕРКА -- Разность диаметров (фильер)
            """

            # меньше диаметр - больше фильер
            if previous_order.spin > order.spin:
                removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
                total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
                total_setup_time += INSERT_SPIN * 1  # Время на установку фильер. 1 последняя
                total_setup_time += CHANGE_BOBBIN  # Время на смену катушки
            # больше диаметр - меньше фильер
            elif previous_order.spin < order.spin:
                removed_spin = 1  # снимаем последнюю
                total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
                total_setup_time += INSERT_SPIN * (
                            order.spin - order.spin - 1)  # время на установку фильер -1, потому 1 уже снята
                total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

            """
                2 ПРОВЕРКА -- Разность проволочек
            """

            dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

            if previous_order.wires_in_sliver < order.wires_in_sliver:
                # Надо протянуть новые проволочки через все фильеры на новом заказе
                total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
            elif previous_order.wires_in_sliver > order.wires_in_sliver:
                # Надо снять проволочки со всех фильер previous_order
                total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE

        previous_order = order

    return total_setup_time


# Функция для вычисления суммарного штрафа за просрочку заказов (можно адаптировать под вашу ситуацию)
def calculate_total_penalty(orders):
    total_penalty = 0

    for order in orders:
        # Некоторая логика для вычисления штрафа за просрочку заказа
        # Ваша логика может отличаться
        # Здесь просто пример, чтобы код скомпилировался
        total_penalty += order[0] * order[1]

    return total_penalty


def optimization(orders: list[TaskForMultik]):

    # Начальное значение параметров (предположим, начинаем с первого заказа)
    initial_guess = (orders[0].spin, orders[0].wires_in_sliver)

    # Оптимизация целевой функции
    result = minimize(objective_function, initial_guess, orders, method='Nelder-Mead')

    # Получение оптимальных параметров
    optimal_params = result.x
    print("Optimal parameters:", optimal_params)

    # Получение минимального значения целевой функции (время настройки + штраф)
    min_objective_value = result.fun
    print("Minimum objective value:", min_objective_value)
