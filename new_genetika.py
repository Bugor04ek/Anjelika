import time
from datetime import datetime
from pickle import GLOBAL
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool


import time
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

TASKS = []


def varAnd(population, toolbox, cxpb, mutpb):
    # Клонирование популяции
    offspring = [toolbox.clone(ind) for ind in population]

    # Сгенерируем заранее случайные числа для скрещивания
    crossover_flags = numpy.random.rand(len(offspring) - 1) < cxpb

    # Параллельное выполнение операций
    with ThreadPoolExecutor() as executor:
        def apply_crossover_and_mutation(i):
            # Скрещивание
            if crossover_flags[i]:
                toolbox.mate(offspring[i], offspring[i + 1])
                del offspring[i].fitness.values
                del offspring[i + 1].fitness.values

            # Мутация
            for equipment_type in offspring[i].keys():
                for equipment in offspring[i][equipment_type]:
                    if len(offspring[i][equipment_type][equipment]) > 1:
                        tools.mutShuffleIndexes(
                            offspring[i][equipment_type][equipment],
                            indpb=1.0 / len(offspring[i][equipment_type][equipment])
                        )
            del offspring[i].fitness.values

            # Пересчет корзин, если изменилось задание на мультике
            # for eq in offspring['multivare']:
            #     multivare_tasks = offspring[i][eq]
            #
            #     # Пересчитываем состав корзин
            #     updated_baskets = calculating_basket(multivare_tasks)
            #
            #     # Обновляем задания на волочилке
            #     for eq1 in offspring['wiredrawing']:
            #         if any(isinstance(task, Basket) for task in offspring['wiredrawing'][eq1]):
            #             for i in range(offspring['wiredrawing'][eq1]):
            #                 if isinstance(offspring['wiredrawing'][eq1][i], Basket):
            #                     offspring['wiredrawing'][eq1][i] = updated_baskets[i]

        executor.map(apply_crossover_and_mutation, range(len(offspring) - 1))

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


def mutate(individual, mutation_rate=0.05):
    # Генерируем заранее случайные числа для мутации
    mutation_flags = numpy.random.rand(len(individual.keys())) < mutation_rate
    for i, (equipment, flag) in enumerate(zip(individual.keys(), mutation_flags)):
        if flag:
            random.shuffle(individual[equipment])
    return individual


def cxOrderedCustom(ind1, ind2):
    """
    Кастомный оператор скрещивания на основе cxOrdered для сложной структуры.
    """

    # Создаем копии родителей для потомков
    # child1, child2 = copy.deepcopy(ind1), copy.deepcopy(ind2)
    child1, child2 = {}, {}

    for equipment_type in ind1.keys():
        for equipment in ind1[equipment_type]:
            tasks_ind1 = ind1[equipment_type][equipment]
            tasks_ind2 = ind2[equipment_type][equipment]
            if len(tasks_ind1) < 2 or len(tasks_ind2) < 2:
                continue

            indices1 = list(range(len(tasks_ind1)))
            indices2 = list(range(len(tasks_ind2)))

            tools.cxUniformPartialyMatched(indices1, indices2, indpb=2.0 / 150)

            child1[equipment] = [tasks_ind1[i] for i in indices1]
            child2[equipment] = [tasks_ind2[i] for i in indices2]

    return child1, child2

# Основная функция запуска алгоритма
def run_genetic_algorithm(pop_size=50, cxpb=0.7, mutpb=0.2, ngen=50):

    TASKS = Task.get_instances_all()

    # константы задачи
    HALL_OF_FAME_SIZE = len(TASKS) * 0.01  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = len(TASKS) // 10  # количество индивидуумов в популяции
    MAX_GENERATIONS = len(TASKS)  # максимальное количество поколений
    P_CROSSOVER = 1  # вероятность скрещивания
    P_MUTATION = 0.05  # вероятность мутации индивидуума
    TASKS_len = len(Task.get_instances_all())

    toolbox = base.Toolbox()
    print(POPULATION_SIZE)

    # Настройка среды DEAP для минимизации времени
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

    # creator.create("Basket", list)
    creator.create("Task", list)
    creator.create("Individual", dict, fitness=creator.FitnessMin, Task=creator.Task)

    toolbox.register("individual", tools.initIterate, creator.Individual, lambda: generate_individual())
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    population = toolbox.population(n=POPULATION_SIZE)

    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", cxOrderedCustom)
    toolbox.register("mutate", mutate, P_MUTATION)

    # Создаем пул процессов
    pool = Pool()
    toolbox.register("map", pool.map)  # Регистрируем параллельную карту

    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("avg", numpy.mean)
    stats.register("min", numpy.min)

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

    # Закрываем пул
    pool.close()
    pool.join()

    print("- Лучшие решения:")
    # Запуск генетического алгоритма с элитизмом
    best_order = hof.items[0]  # массив заказов в виде индексов
    print(best_order)
    return best_order


# Создание начальной популяции на основе заданий
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
    for eq in individual['multivare']:
        task_m = copy.deepcopy(individual['multivare'][eq])
        MultivareTask.calculate_setup_time_all(individual['multivare'][eq])
        updated_baskets.extend(calculating_basket(task_m))

    for basket in updated_baskets:
        ind = individual[basket.equipment_type][basket.equipment.equipment_name]
        ind.insert(random.randint(0, len(ind)), basket)

    time_end = datetime.now()
    print(time_end - time_start)
    return individual


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def get_cost_multivare(ind):
    time = 0
    # map(lambda x: x.capacity * 0 + 8, Equipment.get_instances_by_type(equipment_type='multivare'))
    for eq in ind['multivare']:
        tasks = copy.deepcopy(ind['multivare'][eq])
        for task in tasks:
            time += task.time_setup

    return time


def calculating_basket(task):
    """
    Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
    если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
    :return:
    """

    temp_basket: Basket = copy.deepcopy(Basket(None))
    updated_baskets = []
    # individual = ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name]
    for order in task:

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


def get_cost_drawing(ind, print_logs=False):
    # return 0
    # indexes_baskets = individual.basket
    total_time = 0  # суммарное время перенастроек
    num_downtime = 0  # количество простоев волочилки
    num_uptime = 0  # количесвто простоев мультика
    time_route_to_basket = 0

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

    time_total = 0

    # Параллельно запускаем расчёты для каждого оборудования
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        equipment_types = ['old', 'new', 'al']

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

    for eq in ind['wiredrawing']:
        tasks = ind['wiredrawing'][eq]
        if not any(isinstance(task, Basket) for task in tasks):
            for task in tasks:
                time_total += task.time_setup
        else:
            time_total += get_cost_basket(tasks)

    return time_total


def calculate_setup_time_for_tasks(tasks, filters_dict, eq_type, print_logs=False):
    """Вычисление времени переналадки на одном оборудовании с учётом фильер."""
    time_total = 0
    equipment_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(len(tasks)):
        current_task = tasks[i]

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


def get_cost_basket(tasks_with_basket):

    total_time = 0  # суммарное время перенастроек
    num_downtime = 0  # количество простоев волочилки
    num_uptime = 0  # количесвто простоев мультика
    time_route_to_basket = 0
    time_setup = 0
    baskets = [task for task in tasks_with_basket if isinstance(task, Basket)]
    routes = get_routes(tasks_with_basket)

    reserve_time = baskets[0].time_on_multivare
    num_task = len(tasks_with_basket) - len(baskets)
    for route in range(len(baskets) - 1):
        if len(routes[route]) != 0:
            time_route_to_basket += get_time_route(routes[route], route)
            num_task -= len(routes[route])
        elif num_task != 0:
            total_time += 5000000
            break
        elif num_task == 0:
            num_downtime += baskets[route + 1].time_on_multivare

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

        # total_time += time_route_to_basket
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


def evaluate_fitness(individual):
    multivare_time = get_cost_multivare(individual)
    drawing_time = get_cost_drawing(individual)
    return multivare_time + drawing_time,


def run():
    return run_genetic_algorithm()
