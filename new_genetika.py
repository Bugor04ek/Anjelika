import time
from datetime import datetime
from pickle import GLOBAL
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from collections import defaultdict

import threading
from threading import Lock
import json
import numpy
from deap import base, creator, tools, algorithms
from datetime import datetime, timedelta
import random
import copy

from numpy.random.mtrand import choice

import Equipments
import Tasks
from Tasks import Task, TaskMeta, MultivareTask, WireDrawingTask, Basket
from Equipments import MultivareMachine, WireDrawingMachine, Equipment
from main import equipments

TASKS = []


def varAnd(population, toolbox, cxpb, mutpb):

    offspring = [copy.deepcopy(ind) for ind in population]

    for i in range(1, len(offspring), 2):
        offspring[i - 1], offspring[i] = toolbox.mate(offspring[i - 1], offspring[i], cxpb)
        del offspring[i - 1].fitness.values
        del offspring[i].fitness.values
        offspring[i].Basket = calculating_basket(offspring[i])
        offspring[i - 1].Basket = calculating_basket(offspring[i - 1])

    for i in range(len(offspring)):
        offspring[i] = toolbox.mutate(offspring[i], mutpb)
        del offspring[i].fitness.values
        offspring[i].Basket = calculating_basket(offspring[i])

        # executor.map(apply_crossover_and_mutation, range(len(offspring) - 1))

    return offspring


def eaSimpleWithElitism(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=__debug__):
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    def evaluate_invalid(individuals):
        invalid_ind = [ind for ind in individuals if not ind.fitness.valid]
        if invalid_ind:
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
        return invalid_ind

    if halloffame is None:
        raise ValueError("halloffame parameter must not be empty!")

    evaluate_invalid(population)
    halloffame.update(population)
    hof_size = len(halloffame.items) if halloffame.items else 0

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(population), **record)
    if verbose:
        print(logbook.stream)

    for gen in range(1, ngen + 1):
        offspring = toolbox.select(population, len(population) - hof_size)

        # Вызов varAnd для обработки потомков
        offspring = varAnd(offspring, toolbox, cxpb, mutpb)

        evaluate_invalid(offspring)

        offspring.extend(halloffame.items)
        halloffame.update(offspring)
        population[:] = offspring

        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(offspring) - hof_size, **record)
        if verbose:
            print(logbook.stream)

    return population, logbook


def mutate(individual, indpb):
    # Генерируем заранее случайные числа для мутации
    ind = copy.deepcopy(individual)
    for equipment_type in ind.keys():
        for equipment in ind[equipment_type]:
            ind[equipment_type][equipment], = tools.mutShuffleIndexes(individual[equipment_type][equipment], indpb)
    return ind


def cxOrderedCustom(ind1, ind2, indpb):
    """
    Кастомный оператор скрещивания на основе cxOrdered для сложной структуры.
    """

    # Создаем копии родителей для потомков
    child1, child2 = ind1, ind2
    # child1, child2 = {}, {}

    for equipment_type in ind1.keys():
        for equipment in ind1[equipment_type]:
            tasks_ind1 = ind1[equipment_type][equipment]
            tasks_ind2 = ind2[equipment_type][equipment]
            if len(tasks_ind1) < 2 or len(tasks_ind2) < 2:
                continue

            indices1 = list(range(len(tasks_ind1)))
            indices2 = list(range(len(tasks_ind2)))

            tools.cxUniformPartialyMatched(indices1, indices2, indpb)

            child1[equipment_type][equipment] = [tasks_ind1[i] for i in indices1]
            child2[equipment_type][equipment] = [tasks_ind2[i] for i in indices2]

    return child1, child2


def run_genetic_algorithm(pop_size=50, cxpb=0.7, mutpb=0.2, ngen=50):

    TASKS = Task.get_instances_all()

    # константы задачи
    HALL_OF_FAME_SIZE = len(TASKS) // 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = len(TASKS) // 2  # количество индивидуумов в популяции
    MAX_GENERATIONS = len(TASKS)// 2 # максимальное количество поколений
    P_CROSSOVER = 1  # вероятность скрещивания
    P_MUTATION = 0.05  # вероятность мутации индивидуума
    TASKS_len = len(Task.get_instances_all())

    toolbox = base.Toolbox()
    print(POPULATION_SIZE)

    # Настройка среды DEAP для минимизации времени
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

    creator.create("Basket", list)
    creator.create("Individual", dict, fitness=creator.FitnessMin, Basket=creator.Basket)

    toolbox.register("individual", tools.initIterate, creator.Individual, lambda: generate_individual())
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    population = toolbox.population(n=POPULATION_SIZE)

    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("select", tools.selTournament, tournsize=50)
    toolbox.register("mate", cxOrderedCustom)
    toolbox.register("mutate", mutate)

    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("avg", numpy.mean)
    stats.register("min", numpy.min)
    # stats.register("std", numpy.std) # Дисперсия помогает понять разброс значений приспособленности в популяции, что может быть индикатором разнообразия.

    # Инициализация популяции
    population, logbook = eaSimpleWithElitism(
        population, toolbox,
        cxpb=P_CROSSOVER,
        mutpb=P_MUTATION,
        ngen=MAX_GENERATIONS,
        stats=stats,
        halloffame=hof,
        verbose=True
    )

    print("- Лучшие решения:")
    # Запуск генетического алгоритма с элитизмом
    best_order = hof.items[0]  # массив заказов в виде индексов
    # print(best_order)
    formatted_solution = format_best_solution(best_order)
    print(formatted_solution)
    return best_order


def format_best_solution(best_order):
    """Форматирует вывод для лучшего решения."""
    formatted_output = []

    for equipment_type, equipment_data in best_order.items():
        formatted_output.append(f"Тип оборудования: {equipment_type}")
        for equipment_name, tasks in equipment_data.items():
            formatted_output.append(f"  Оборудование: {equipment_name}")
            for task in tasks:
                if isinstance(task, Basket):
                    # Форматируем данные корзины
                    basket_details = (
                        f"    Корзина (длина: {task.sum_basket}, диаметр: {task.diameter}, "
                        f"время работы заказов: {task.time_on_multivare}):"
                    )
                    formatted_output.append(basket_details)
                    for basket_task in task.orders:
                        formatted_output.append(
                            f"      - Заказ: {basket_task.account_number}, "
                            f"Диаметр: {basket_task.diameter}, "
                            f"Маршрут фильер: {basket_task.spin_road}, "
                            f"Комментарий к перенастройке: {basket_task.comment_setup}"
                        )
                elif isinstance(task, MultivareTask):
                    # Форматируем данные заказа на мультивайер
                    formatted_output.append(
                        f"    Заказ: {task.account_number}, "
                        f"Диаметр: {task.diameter}, "
                        f"Жил: {task.number_of_veins}, "
                        f"Корзины: {round(task.num_basket, 2)}, "
                        f"Маршрут фильер: {task.spin_road}, "
                        f"Комментарий к перенастройке: {task.comment_setup}"
                    )
                else:
                    # Форматируем обычный заказ
                    diameter = getattr(task, "voloka", "Не указано")
                    spin_road = getattr(task, "spin_road", [])
                    comment_setup = getattr(task, "comment_setup", "Нет комментария")
                    formatted_output.append(
                        f"    Заказ: {task.order.account_number}, Диаметр: {diameter}, Штраф за ожидание: {task.time_penalty} "
                        f"Маршрут фильер: {spin_road}, Комментарий к перенастройке: {comment_setup}"
                    )

    return "\n".join(formatted_output)


# # Создание начальной популяции на основе заданий
def generate_individual():
    """Создает индивида с распределением задач по оборудованию."""
    # Task_c = copy.deepcopy(Task)
    # TaskMeta_c = copy.deepcopy(TaskMeta)
    # Выбираем рандомное оборудование на задание из подходящих оборудований
    time_start = datetime.now()
    tasks = TaskMeta.get_instances_all()  # Получаем список задач
    # random.shuffle(tasks)  # Перемешиваем задачи

    Task.assign_tasks_to_equipment(tasks)

    # TaskMeta.get_instances_by_type(equipment_type='multivare')
    # TaskMeta.get_instances_by_type(equipment_type='wiredrawing')

    # задание на каждый тип оборудований
    individual = {}
    for eq in Equipment.get_all_instances():
        for equipment_type in eq.equipment_type:
            if individual.get(equipment_type, None) is None:
                individual[equipment_type] = {}
            task_c = copy.deepcopy(TaskMeta.get_instances_by_type(equipment=eq))
            individual[equipment_type][eq.equipment_name] = random.sample(task_c, len(task_c))

    updated_baskets = []
    updated_baskets.extend(calculating_basket(individual))

    for i, basket in enumerate(updated_baskets):
        ind = individual[basket.equipment_type][basket.equipment.equipment_name]
        ind.insert(random.randint(0, len(ind)), Basket(None))

    individual['basket'] = updated_baskets
    time_end = datetime.now()
    print(f"Время выполнения generate_individual: {time_end - time_start}")
    return individual


def evaluate_fitness(individual: dict):
    if len(individual.Basket) == 0:
        individual.Basket = individual.pop('basket', [])
    multivare_time = get_cost_multivare(individual)
    drawing_time = get_cost_drawing(individual)
    return multivare_time + drawing_time,


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def get_cost_multivare(ind):
    time_total = 0
    # map(lambda x: x.capacity * 0 + 8, Equipment.get_instances_by_type(equipment_type='multivare'))
    for eq in ind['multivare']:
        tasks = ind['multivare'][eq]
        time_total += sum([task.time_setup for task in tasks])

    return time_total


def get_cost_drawing(ind, print_logs=False):

    time_total = 0

    for eq in ind['wiredrawing']:
        tasks = ind['wiredrawing'][eq]
        WireDrawingTask.calculate_setup_time_all(tasks)
        if not any(isinstance(task, Basket) for task in tasks):
            time_total += sum([task.time_setup for task in tasks])
        else:
            time_total += get_cost_basket(tasks, ind.Basket)


    filters_json = 'Оборудование/Фильеры.json'
    # Чтение JSON-файла в массив
    with open(filters_json, 'r', encoding='utf-8') as file:
        filters_array = json.load(file)

    # Получаем сегодняшний день в 0:00
    today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Создаем словарь фильер с ключом "Диаметр"
    filters_dict = {}
    for filter_item in filters_array:
        filter_item["ВремяОсвобождения"] = today_midnight
        filters_dict[filter_item['Диаметр']] = {"Информация": filter_item}

    # Параллельно запускаем расчёты для каждого оборудования
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        equipment_types = list(ind['wiredrawing'].keys())

        # Перемешиваем волочилки в случайном порядке
        random.shuffle(equipment_types)

        for eq_type in equipment_types:
            add_missing_filters(filters_dict, ind['wiredrawing'][eq_type])
            future = executor.submit(
                calculate_setup_time_for_tasks,
                ind['wiredrawing'][eq_type],
                filters_dict,
                eq_type,
                print_logs  # Передаем флаг логирования
            )
            futures.append(future)

        # Ждём завершения всех потоков и суммируем результаты
        for future in futures:
            time_total += future.result()


    return time_total


def calculating_basket(ind):
    """
    Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
    если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
    :return:
    """
    updated_baskets = []
    for eq in ind['multivare']:
        e = Equipment.get_instances_by_type(equipment_name=eq)[0]
        e.capacity = e.remaining_basket_length
        task_m = ind['multivare'][eq]
        MultivareTask.calculate_setup_time_all(task_m)
        temp_basket: Basket = copy.deepcopy(Basket(None))
        # individual = ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name]
        for order in task_m:

            if order.equipment.capacity - order.num_basket >= 0:
                temp_basket.append(order, order.num_basket)
                order.equipment.capacity -= order.num_basket  # сколько нужно до 8 корзин
                # Если со следующим заказом получается меньше 8 корзин, но он занимает сам по себе больше 8 корзин
            else:
                temp_basket.append(order, order.equipment.capacity)
                # ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name].insert(random.randint(0, len(individual)), temp_basket)
                updated_baskets.append(temp_basket)
                num_basket = order.num_basket - order.equipment.capacity
                while num_basket > 8:
                    temp_basket = copy.deepcopy(Basket(order, 8))
                    # ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name].insert(random.randint(0, len(individual)), temp_basket)
                    updated_baskets.append(temp_basket)
                    num_basket -= 8

                order.equipment.capacity = 8 - num_basket
                temp_basket = copy.deepcopy(Basket(order, num_basket))
        else:
            if len(temp_basket.orders) > 0:
                # Task.assign_tasks_to_equipment(temp_basket)
                # individual.insert(random.randint(0, len(individual)), temp_basket)
                updated_baskets.append(temp_basket)

    return updated_baskets
# Функция для обработки spin_road и добавления новых фильер


def add_missing_filters(filters_dict, tasks):
    # Получаем сегодняшний день в 0:00
    today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for task in tasks:
        spin_road = task.spin_road
        # Если spin_road содержит вложенный список (для old), разворачиваем его
        if isinstance(spin_road, list) and isinstance(spin_road[0], list):
            spin_road = [diameter for sublist in spin_road for diameter in sublist]
        elif not isinstance(spin_road, list):
            spin_road = [spin_road]

        # Проверяем и добавляем отсутствующие фильеры
        for filter_diameter in spin_road:
            if filter_diameter == 0:  # Пропускаем диаметры равные 0
                continue
            if filter_diameter not in filters_dict:
                # Добавляем фильеру с минимальными параметрами
                filters_dict[filter_diameter] = {
                    "Информация": {
                        "Диаметр": filter_diameter,
                        "ИспользуетсяВоборудованиях": [],
                        "Вработе": False,
                        "Количество": 1,
                        "БудетНаходитьсяВРаботе": 0,
                        "ВремяОсвобождения": today_midnight
                    }
                }
                # print(f"Добавлена фильера с диаметром {filter_diameter}")

 
def calculate_setup_time_for_tasks(tasks, filters_dict, eq_type, print_logs=False):
    """Вычисление времени переналадки на одном оборудовании с учётом фильер."""
    time_total = 0
    equipment_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(len(tasks)):
        current_task = copy.deepcopy(tasks[i])

        # Обработка spin_road
        current_task.spin_road = current_task.spin_road[0] if isinstance(current_task.spin_road[0], list) else current_task.spin_road

        # Вывод списка фильеров, необходимых для текущего заказа
        if print_logs:
            print(
                f"Для текущего заказа нужны фильеры: {current_task.spin_road} и время его выполнения - {current_task.time_work} минут.")

        # Проверяем доступность фильер
        all_filters_available = True
        local_penalty_time = 0
        for filter_diameter in current_task.spin_road:
            # Пропускаем фильеры с диаметром 0
            if filter_diameter == 0:
                continue

            if filter_diameter not in filters_dict:
                if print_logs:
                    print(f"Фильера {filter_diameter} отсутствует в справочнике!")
                continue

            filter_info = filters_dict[filter_diameter]["Информация"]

            # Проверяем, доступна ли фильера
            if filter_info["Количество"] <= 0:
                all_filters_available = False
                remaining_time = max(
                    0,
                    (filter_info["ВремяОсвобождения"] - equipment_time).total_seconds() / 60
                )

                local_penalty_time += remaining_time
                tasks[i].time_penalty += local_penalty_time
                if print_logs:
                    print(f"Фильера {filter_diameter} занята, штраф за ожидание: {remaining_time} минут.")
                break

        # Если фильеры недоступны, добавляем штраф и переходим к следующему заказу
        if not all_filters_available:
            time_total += local_penalty_time  # Только штраф за оставшееся время
            continue

        # Обновляем время выполнения оборудования
        task_time = current_task.time_work
        equipment_time += timedelta(minutes=task_time)
        time_total += task_time

        # Обновляем информацию о фильерах
        for filter_diameter in current_task.spin_road:
            if filter_diameter == 0:  # Пропускаем фильеры с диаметром 0
                continue
            if filter_diameter in filters_dict:
                filter_info = filters_dict[filter_diameter]["Информация"]
                filter_info["Количество"] -= 1  # Уменьшаем доступное количество
                filter_info["ВремяОсвобождения"] = equipment_time  # Обновляем время освобождения фильеры
                if print_logs:
                    print(f"Фильера {filter_diameter} используется, осталось {filter_info['Количество']}.")

        # Освобождаем фильеры после выполнения задания
        for filter_diameter in current_task.spin_road:
            if filter_diameter == 0:  # Пропускаем фильеры с диаметром 0
                continue
            if filter_diameter in filters_dict:
                filter_info = filters_dict[filter_diameter]["Информация"]
                filter_info["Количество"] += 1  # Возвращаем доступное количество
                if filter_info["Количество"] == 1:
                    filter_info["ВремяОсвобождения"] = equipment_time
                if print_logs:
                    print(f"Фильера {filter_diameter} освобождена, теперь доступно {filter_info['Количество']}.")

        if print_logs:
            print(f"Оборудование {eq_type}: заказ {i} выполнен. Текущее время: {equipment_time.time()}")

    if print_logs:
        print(f"Задания для оборудования {eq_type} просчитаны")
    return time_total


def get_cost_basket(tasks_with_basket, baskets):

    total_time = 0            # суммарное время перенастроек
    num_downtime = 0          # время простоев волочилки
    num_uptime = 0            # время простоев мультика
    time_route_to_basket = 0  # время между корзинами на волочилке

    # baskets = [task for task in tasks_with_basket if isinstance(task, str)]
    routes = get_routes(tasks_with_basket)

    reserve_time = baskets[0].time_on_multivare
    num_task = len(tasks_with_basket) - len(baskets)
    for route in range(len(baskets) - 1):
        time_route_to_basket += get_time_route(routes[route], route)
        num_task -= len(routes[route])

        if reserve_time < time_route_to_basket < reserve_time + baskets[route + 1].time_on_multivare:
            reserve_time = baskets[route + 1].time_on_multivare - (time_route_to_basket - reserve_time)
            if reserve_time < WireDrawingMachine.W:
                num_downtime += WireDrawingMachine.W - reserve_time
        elif time_route_to_basket < reserve_time:
            num_downtime += reserve_time - time_route_to_basket
            reserve_time = baskets[route + 1].time_on_multivare
        elif time_route_to_basket > reserve_time + baskets[route + 1].time_on_multivare - WireDrawingMachine.W:
            num_uptime += time_route_to_basket - (reserve_time + baskets[route + 1].time_on_multivare - WireDrawingMachine.W)
            reserve_time = baskets[route + 1].time_on_multivare

        total_time += time_route_to_basket
        time_route_to_basket = 0

    else:

        time_route_to_basket += get_time_route(routes[-2], routes.index(routes[-2]))

        reserve_time = baskets[-1].time_on_multivare

        if reserve_time < time_route_to_basket < reserve_time + baskets[-1].time_on_multivare:
            pass
        elif time_route_to_basket < reserve_time:
            num_downtime += reserve_time - time_route_to_basket
        elif time_route_to_basket > reserve_time:
            num_uptime += time_route_to_basket - reserve_time

        total_time += time_route_to_basket

    return total_time + num_downtime + num_uptime


def get_routes(tasks):
    """
        Разбиваем индивида (очередь) на маршруты от корзины до корзины
        :param tasks: текущая очередь
        :return: [[]]
        """
    routes = []
    route = []

    # loop over all indices in the list:
    for task in tasks:

        # index is part of the current route:
        if not isinstance(task, Basket):
            route.append(task)

        # separator index - route is complete:
        else:
            routes.append(route)
            route = []  # reset route

    # append the last route:
    if route:
        routes.append(route)

    return routes


def get_time_route(tasks: [WireDrawingTask], number_route: int):
    """
    Считается время работы + перенастройки между корзинами. route имеет вид [[],[],[]], поэтому, если number_route == 0,
    то перенастройки с корзины не будет, т.к. это первый путь. Запятые символизируют корзины
    :param tasks: задания перед корзинами
    :param number_route: номер пути
    :return: суммарное время работы
    """
    time = 0

    for task in tasks:
        time += task.time_work + task.time_setup

    # добавляем время на изготовление 8 корзин
    time += (WireDrawingMachine.W if number_route else 0)

    return time


def run():
    return run_genetic_algorithm()
