import time
from datetime import datetime
from pickle import GLOBAL
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Pool
from collections import defaultdict
import multiprocessing

import threading
from threading import Lock
import json
import numpy as np
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
    offspring = [toolbox.clone(ind) for ind in population]

    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            offspring[i - 1], offspring[i] = toolbox.mate(offspring[i - 1], offspring[i], cxpb)
            del offspring[i - 1].fitness.values
            del offspring[i].fitness.values
            offspring[i].Basket = calculating_basket(offspring[i])
            offspring[i - 1].Basket = calculating_basket(offspring[i - 1])

    for i in range(len(offspring)):
        offspring[i] = toolbox.mutate(offspring[i], mutpb)
        del offspring[i].fitness.values
        offspring[i].Basket = calculating_basket(offspring[i])

    return offspring


def eaSimpleWithElitism(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=True):
    """
    Реализует генетический алгоритм с элитизмом.

    Параметры:
    - population: начальная популяция.
    - toolbox: объект Toolbox, содержащий зарегистрированные операторы.
    - cxpb: вероятность скрещивания.
    - mutpb: вероятность мутации.
    - ngen: количество поколений.
    - stats: объект Statistics для сбора статистики.
    - halloffame: объект HallOfFame для сохранения элитных индивидов.
    - verbose: флаг для вывода логов.

    Возвращает:
    - population: финальная популяция.
    - logbook: логбук с собранной статистикой.
    """

    # Инициализация логбука
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is None:
        raise ValueError("halloffame parameter must not be empty!")

    halloffame.update(population)
    hof_size = len(halloffame.items)

    # Запись статистики начального поколения
    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # Основной цикл по поколениям
    for gen in range(1, ngen + 1):
        # Селекция потомков (за вычетом элиты)
        offspring = toolbox.select(population, len(population) - hof_size)

        # Применение скрещивания и мутации
        offspring = varAnd(offspring, toolbox, cxpb, mutpb)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Оценка приспособленности новых потомков
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Добавление элитных индивидов из Hall of Fame
        offspring.extend(halloffame.items)
        halloffame.update(offspring)

        # Обновление популяции
        population[:] = offspring

        # Сбор и запись статистики
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
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


def mate(ind1, ind2, indpb):
    """
    Кастомный оператор скрещивания на основе cxOrdered для сложной структуры.
    """

    # Создаем копии родителей для потомков
    child1, child2 = ind1, ind2
    # child1, child2 = {}, {}

    for equipment_type in ind1.keys():
        for equipment in ind1[equipment_type]:
            tasks_ind1 = copy.deepcopy(ind1[equipment_type][equipment])
            tasks_ind2 = copy.deepcopy(ind2[equipment_type][equipment])

            if len(tasks_ind1) < 2 or len(tasks_ind2) < 2:
                continue
            unique_nums = list(np.unique(tasks_ind1 + tasks_ind2, True))

            indices1 = [np.where(unique_nums[0] == task)[0][0] for task in tasks_ind1]
            indices2 = [np.where(unique_nums[0] == task)[0][0] for task in tasks_ind2]
            if len(indices1) != len(indices2):
                continue
            try:
                tools.cxOrdered(indices1, indices2)
            except:
                continue

            child1[equipment_type][equipment] = [unique_nums[0][index] for index in indices1]
            child2[equipment_type][equipment] = [unique_nums[0][index] for index in indices1]

    return child1, child2


def run_genetic_algorithm():
    TASKS = Task.get_instances_all()

    # константы задачи
    HALL_OF_FAME_SIZE = len(TASKS) // 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = len(TASKS)  # количество индивидуумов в популяции
    MAX_GENERATIONS = 10    # максимальное количество поколений
    P_CROSSOVER = 1  # вероятность скрещивания
    P_MUTATION = 0.05  # вероятность мутации индивидуума

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
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", mate)
    toolbox.register("mutate", mutate)

    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("avg", np.mean)
    stats.register("min", np.min)
    # stats.register("std", numpy.std) # Дисперсия помогает понять разброс значений приспособленности в популяции, что может быть индикатором разнообразия.

    # # Создание пула процессов для параллельной оценки
    # pool = multiprocessing.Pool()
    #
    # # Регистрация метода map из пула процессов
    # toolbox.register("map", pool.map)

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

    # # Закрытие пула процессов
    # pool.close()
    # pool.join()

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
        total_time = 0
        for equipment_name, tasks in equipment_data.items():
            formatted_output.append(f"  Оборудование: {equipment_name}")
            for task in tasks:
                if isinstance(task, Basket):
                    # Форматируем данные корзины
                    basket_details = (
                        f"  Время работы группы заказов {total_time} \n  Корзина (длина: {task.sum_basket}, диаметр: {task.diameter}, "
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
                    total_time = 0
                    total_time += WireDrawingMachine.W
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
                    if equipment_name == 'new':
                        total_time += task.time_work + task.time_setup
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
        filters_dict[filter_item['Диаметр']] = {"ВремяОкончанияРаботы": today_midnight, "ИспользуетсяОборудованием": "",
                                                "ИспользуетсяЗаказом": ""}
        # filters_dict[filter_item['Диаметр']] = {"Информация": filter_item}

    # Заполняет словарь фильер, фильерам из заказов (в заказах могут быть такие, которых нет в словаре)
    add_missing_filters(filters_dict, ind['wiredrawing'])
    filters_dict = dict(sorted(filters_dict.items()))

    # Получаем все заказы в индивиде по опр оборудованию
    for eq_type in list(ind['wiredrawing'].keys()):
        setup_time_begin_end(ind['wiredrawing'][eq_type])

    # Параллельно запускаем расчёты для каждого оборудования
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        equipment_types = list(ind['wiredrawing'].keys())

        # Перемешиваем волочилки в случайном порядке
        random.shuffle(equipment_types)

        for eq_type in equipment_types:
            future = executor.submit(
                calculate_setup_time_for_tasks,
                ind['wiredrawing'][eq_type],
                filters_dict,
                eq_type,
                print_logs  # Передаем флаг логирования
            )
            # print(f"Запустили поток {eq_type}")
            futures.append(future)

        # Ждём завершения всех потоков и суммируем результаты
        for future in futures:
            time_total += future.result()

    # print(f"Закрыли все потоки")
    return time_total


def calculating_basket(ind):
    """
    Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
    если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
    :return:
    """
    updated_baskets = []
    for eq in ind['multivare']:
        task_m = ind['multivare'][eq]
        for order in task_m:
            order.equipment.capacity = order.equipment.remaining_basket_length
        MultivareTask.calculate_setup_time_all(task_m)
        temp_basket: Basket = copy.deepcopy(Basket(None))
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


def add_missing_filters(filters_dict, ind):
    # Получаем сегодняшний день в 0:00
    today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for eq in ind.keys():

        for task in ind[eq]:
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
                    filters_dict[filter_diameter] = {"ВремяОкончанияРаботы": today_midnight,"ИспользуетсяОборудованием": "", "ИспользуетсяЗаказом": "" }
                    # print(f"Добавлена фильера с диаметром {filter_diameter}")


# Функция для установки времени начала и конца заказа
def setup_time_begin_end(tasks):
    for i in range(len(tasks)):
        tasks[i].time_begin = tasks[i - 1].time_ending + timedelta(minutes = tasks[i].time_setup) # Время начала заказа - время конца предыдущего заказа + время перенастройки
        tasks[i].time_ending = tasks[i].time_begin + timedelta(minutes = tasks[i].time_work)       # Время конца заказа - время начала текущего заказа + время в работе
    return tasks


def calculate_setup_time_for_tasks(tasks, filters_dict, eq_type, print_logs=False):
    """Вычисление времени переналадки на одном оборудовании с учётом фильер."""
    time_total = 0
    general_penalty = 0
    empty_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(len(tasks)):

        all_free = True
        filters_in_use = {}

        if tasks[0].equipment.equipment_name == "old":
            spins = tasks[i].spin_road
        else:
            spins = [tasks[i].spin_road]

        for road in spins:

            for spin in road:

                if spin == 0: continue

                if filters_dict[spin]['ВремяОкончанияРаботы'] == empty_time:
                    pass
                else:
                    # мб тут захватить и отдать в all_free else что бы пока собирали список занятых, его не переписали
                    all_free = False
                    filters_in_use[spin] = spin

            if all_free:
                for spin in road:
                    if spin == 0: continue
                    # не забыть сделать захват словаря фильер
                    filters_dict[spin]['ВремяОкончанияРаботы'] += timedelta(minutes=tasks[i].time_work)
                    filters_dict[spin]['ИспользуетсяОборудованием'] = tasks[i].equipment.equipment_name

                    if isinstance(tasks[i], Basket):
                        filters_dict[spin]['ИспользуетсяЗаказом'] = "Корзина"
                    else:
                        filters_dict[spin]['ИспользуетсяЗаказом'] = tasks[i].account_number
            else:
                # Какая-то из фильер занята
                filters_time = {}

                for filters in filters_in_use:
                    filters_time[filters] = (filters_dict[filters]['ВремяОкончанияРаботы'] - tasks[
                        i].time_begin).total_seconds() / 60  # Время между концом работы фильеры и началом заказа (сколько ждать)

                if max(filters_time.values()) > 0:
                    tasks[i].time_penalty = max(
                        filters_time.values())  # Максимальное время из занятых, т.к её придется ждать для полного маршрута

                for filters in filters_in_use:
                    filters_dict[filters]['ВремяОкончанияРаботы'] = tasks[i].time_ending + timedelta(
                        minutes=tasks[i].time_penalty)  # Фильера освободиться через время окончания заказа + штраф

        general_penalty += tasks[i].time_penalty  # Общий штраф всей очереди

    return ((tasks[-1].time_ending - tasks[
        0].time_ending).total_seconds() / 60) + general_penalty  # Общее время = Время от начала первого до конца последнего + сумма всех штрафов


def get_cost_basket(tasks_with_basket, baskets):
    total_time = 0  # суммарное время перенастроек
    num_downtime = 0  # время простоев волочилки
    num_uptime = 0  # время простоев мультика
    time_route_to_basket = 0  # время между корзинами на волочилке

    # baskets = [task for task in tasks_with_basket if isinstance(task, str)]
    routes = get_routes(tasks_with_basket, baskets)

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
            num_uptime += time_route_to_basket - (
                        reserve_time + baskets[route + 1].time_on_multivare - WireDrawingMachine.W)
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

    return total_time + num_downtime * 1.5 + num_uptime * 1.5


def get_routes(tasks, baskets):
    """
        Разбиваем индивида (очередь) на маршруты от корзины до корзины
        :param tasks: текущая очередь
        :return: [[]]
        """
    routes = []
    route = []

    # итератор для вставки корзин вместо пустых заглушек
    b = 0
    # loop over all indices in the list:
    for i, task in enumerate(tasks):

        # index is part of the current route:
        if not isinstance(task, Basket):
            route.append(task)

        # separator index - route is complete:
        else:
            tasks[i] = baskets[b]
            b += 1
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
