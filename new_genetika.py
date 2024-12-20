import os
import time
from datetime import datetime
from pickle import GLOBAL
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Pool
from collections import defaultdict
import multiprocessing
import concurrent



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
settings = None
filters_array = []


# Обновление остатка корзин в файле настроек
def update_remaining_basket_length(new_length):
    """
    Обновляет значение REMAINING_BASKET_LENGTH в JSON-файле настроек.
    Если файл не существует, создает его с дефолтными настройками.

    :param new_length: Новое значение для REMAINING_BASKET_LENGTH
    """
    settings_path = os.path.join("Equipment", "settings.json")

    # Проверяем наличие файла
    if not os.path.exists(settings_path):
        # Дефолтные настройки, если файл отсутствует
        default_settings = {
            "HALL_OF_FAME_SIZE": 0.06,
            "POPULATION_SIZE": 1,
            "MAX_GENERATIONS": 0.09,
            "P_CROSSOVER": 0.8,
            "P_MUTATION": 0.05,
            "MULTITHREADING": True,
            "REMAINING_BASKET_LENGTH": 8,
            "CORES": 2
        }

        # Создаем директорию, если ее нет
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)

        # Записываем дефолтные настройки в файл
        with open(settings_path, 'w') as file:
            json.dump(default_settings, file, indent=4)

    # Читаем текущие настройки из файла
    with open(settings_path, 'r') as file:
        settings = json.load(file)

    # Обновляем значение REMAINING_BASKET_LENGTH
    settings["REMAINING_BASKET_LENGTH"] = new_length

    # Сохраняем обновленные настройки обратно в файл
    with open(settings_path, 'w') as file:
        json.dump(settings, file, indent=4)

    print(f"REMAINING_BASKET_LENGTH успешно обновлено на {new_length}.")


# Получение значений для Генетического Алгоритма
def load_settings():
    # Путь к файлу настроек
    settings_path = os.path.join("Equipment", "settings.json")

    # Дефолтные настройки
    default_settings = {
        "HALL_OF_FAME_SIZE": 0.06,
        "POPULATION_SIZE": 1,
        "MAX_GENERATIONS": 0.09,
        "P_CROSSOVER": 0,
        "P_MUTATION": 0.05,
        "MULTITHREADING": True,
        "REMAINING_BASKET_LENGTH": 8,
        "CORES": 2
    }

    # Проверяем, существует ли файл настроек
    if not os.path.exists(settings_path):
        # Создаем файл с дефолтными настройками
        with open(settings_path, "w", encoding="utf-8") as file:
            json.dump(default_settings, file, indent=4, ensure_ascii=False)
        print(f"Файл настроек не найден. Создан файл с дефолтными значениями: {settings_path}")
        return default_settings

    # Если файл существует, загружаем настройки из него
    with open(settings_path, "r", encoding="utf-8") as file:
        settings = json.load(file)

    # print(f"Загружены настройки из файла: {settings_path}")
    return settings

def get_filters():
    filters_json = 'Оборудование/Фильеры.json'
    # Чтение JSON-файла в массив
    with open(filters_json, 'r', encoding='utf-8') as file:
        filters_array = json.load(file)
    return filters_array

def varAnd(population, toolbox, cxpb, mutpb):
    offspring = [toolbox.clone(ind) for ind in population]

    for i in range(1, len(offspring)):
        if random.random() < cxpb:
            offspring[i] = toolbox.mate(offspring[i])
            del offspring[i].fitness.values
            offspring[i].Basket = calculating_basket(offspring[i])

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
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        # Получаем количество ядер из настроек
        max_cores = multiprocessing.cpu_count()
        cores = settings.get("CORES", 1)
        if cores > max_cores:
            cores = max_cores

        # Используем ProcessPoolExecutor для выполнения в нескольких процессах
        with ProcessPoolExecutor(max_workers=cores) as executor:
            # map автоматически распределяет задачи между процессами
            fitnesses = executor.map(fit_fun, invalid_ind, [toolbox] * len(invalid_ind))

        # Присваиваем значения приспособленности каждому индивиду
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


def fit_fun(ind, toolbox):
    return toolbox.evaluate(ind)


def mutate(individual, indpb):
    # Генерируем заранее случайные числа для мутации
    ind = copy.deepcopy(individual)
    for equipment_type in ind.keys():
        for equipment in ind[equipment_type]:
            ind[equipment_type][equipment], = tools.mutShuffleIndexes(individual[equipment_type][equipment], indpb)
    return ind


def mate(ind1):
    """
    Кастомный оператор скрещивания на основе cxOrdered для сложной структуры.
    """

    # Создаем копии родителей для потомков
    child1 = copy.deepcopy(ind1)

    for equipment_type in child1.keys():
        for equipment in child1[equipment_type]:
            tasks_ind1 = child1[equipment_type][equipment]

            if len(tasks_ind1) < 2:
                continue

            t_task1 = random.choice(tasks_ind1)
            if len(t_task1.acceptable_equipment) == 1:
                continue

            best_num_group = {}
            for eq in t_task1.acceptable_equipment:
                if equipment_type == 'multivare':
                    best_num_group[eq.equipment_name] = len(
                        [task for task in tasks_ind1 if task.spin_road[0] == t_task1.spin_road[0]])
                elif equipment_type == 'wiredrawing':
                    best_num_group[eq.equipment_name] = len(
                        [task for task in tasks_ind1 if task.voloka == t_task1.voloka])

            best_eq = sorted(best_num_group.items(), key=lambda x: x[1])[0][0]
            if best_eq == t_task1.equipment.equipment_name:
                continue

            child1[equipment_type][equipment].remove(t_task1)
            child1[equipment_type][best_eq].append(t_task1)

    return child1

def generate_individual_wrapper():
    return generate_individual()

def get_fitness_values(ind):
    return ind.fitness.values


def run_genetic_algorithm():
    TASKS = Task.get_instances_all()

    # Загрузка настроек из JSON-файла
    global settings
    settings = load_settings()
    global filters_array
    filters_array = get_filters()

    # константы задачи
    HALL_OF_FAME_SIZE = round((len(TASKS) * settings.get("HALL_OF_FAME_SIZE", 2)))  # Количество лучших индивидуумов
    POPULATION_SIZE = round(len(TASKS) * settings.get("POPULATION_SIZE", 1))  # количество индивидуумов в популяции
    MAX_GENERATIONS = round(len(TASKS) * settings.get("MAX_GENERATIONS", 10))  # Максимальное количество поколений
    P_CROSSOVER = settings.get("P_CROSSOVER", 0)  # Вероятность скрещивания
    P_MUTATION = settings.get("P_MUTATION", 0.05)  # Вероятность мутации
    MULTITHREADING = settings.get("MULTITHREADING", 1)  # Многопоточность

    print("Настройки:")
    print(f"HALL_OF_FAME_SIZE: {HALL_OF_FAME_SIZE}")
    print(f"POPULATION_SIZE: {POPULATION_SIZE}")
    print(f"MAX_GENERATIONS: {MAX_GENERATIONS}")
    print(f"P_CROSSOVER: {P_CROSSOVER}")
    print(f"P_MUTATION: {P_MUTATION}")
    print(f"MULTITHREADING: {MULTITHREADING}")
    print(f"REMAINING_BASKET_LENGTH: {settings.get('REMAINING_BASKET_LENGTH', 8)}")
    print(f"CORES: {settings.get('CORES', 2)}")
    print(f"MAX_CORES: {multiprocessing.cpu_count()}\n")

    toolbox = base.Toolbox()

    # Настройка среды DEAP для минимизации времени
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

    creator.create("Basket", list)
    creator.create("Individual", dict, fitness=creator.FitnessMin, Basket=creator.Basket)

    toolbox.register("individual", tools.initIterate, creator.Individual, generate_individual_wrapper)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    population = toolbox.population(n=POPULATION_SIZE)

    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", mate)
    toolbox.register("mutate", mutate)

    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(get_fitness_values)

    stats.register("avg", np.mean)
    stats.register("min", np.min)
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
    update_remaining_basket_length((8 - best_order.Basket[-1].sum_basket))
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

                    Name = "Корзина"
                    diameter = getattr(task, "voloka", "Не указано")
                    spin_road = getattr(task, "spin_road", [])
                    comment_setup = getattr(task, "comment_setup", "Нет комментария")
                    penalty = getattr(task, "time_penalty", "")
                    waiting_order = getattr(task, "waiting_for_order", "")
                    waiting_equipment = getattr(task, "waiting_for_equipment", "")
                    waiting_filter = getattr(task, "waiting_for_filter", "")
                    time_on_multivare = getattr(task, "time_on_multivare", "")
                    remaining_basket_length = getattr(task, "sum_basket", "")
                    time_work = getattr(task, "time_work", "")
                    time_setup = getattr(task, "time_setup", "")
                    task.total_time = total_time

                    formatted_output.append(
                        f"    Время работы группы заказов: {total_time}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup}, Корзина (длина: {task.sum_basket}, Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
                        f"Маршрут фильер: {spin_road}, Комментарий к перенастройке: {comment_setup}, Время работы заказов на мультике: {time_on_multivare}"
                    )

                    # formatted_output.append(basket_details)
                    for basket_task in task.orders:
                        Name = getattr(basket_task, "order.account_number", "")
                        diameter = getattr(basket_task, "diameter", "Не указано")
                        spin_road = getattr(basket_task, "spin_road", [])
                        comment_setup = getattr(basket_task, "comment_setup", "Нет комментария")
                        penalty = getattr(basket_task, "time_penalty", "")
                        waiting_order = getattr(basket_task, "waiting_for_order", "")
                        waiting_equipment = getattr(basket_task, "waiting_for_equipment", "")
                        waiting_filter = getattr(basket_task, "waiting_for_filter", "")
                        time_work = getattr(task, "time_work", "")
                        time_setup = getattr(task, "time_setup", "")

                        formatted_output.append(
                            f"      Заказ: {Name}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup}, Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
                            f"Маршрут фильер: {spin_road}, Комментарий к перенастройке: {comment_setup}"
                        )
                    total_time = 0
                    total_time += WireDrawingMachine.W
                elif isinstance(task, MultivareTask):
                    # Форматируем данные заказа на мультивайер
                    diameter = getattr(task, "diameter", "Не указано")
                    spin_road = getattr(task, "spin_road", [])
                    comment_setup = getattr(task, "comment_setup", "Нет комментария")
                    penalty = getattr(task, "time_penalty", "")
                    waiting_order = getattr(task, "waiting_for_order", "")
                    waiting_equipment = getattr(task, "waiting_for_equipment", "")
                    waiting_filter = getattr(task, "waiting_for_filter", "")
                    number_of_veins = getattr(task, "number_of_veins", "")
                    num_basket = getattr(task, "num_basket", "")
                    time_work = getattr(task, "time_work", "")
                    time_setup = getattr(task, "time_setup", "")

                    formatted_output.append(
                        f"    Заказ: {task.order.account_number}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup}, Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
                        f"Маршрут фильер: {spin_road}, Комментарий к перенастройке: {comment_setup}, Кол-во жил: {number_of_veins}, Корзины: {round(num_basket, 2)}"
                    )
                else:
                    if equipment_name == 'new':
                        total_time += task.time_work + task.time_setup
                    # Форматируем обычный заказ
                    diameter = getattr(task, "voloka", "Не указано")
                    spin_road = getattr(task, "spin_road", [])
                    comment_setup = getattr(task, "comment_setup", "Нет комментария")
                    penalty = getattr(task, "time_penalty", "")
                    waiting_order = getattr(task, "waiting_for_order", "")
                    waiting_equipment = getattr(task, "waiting_for_equipment", "")
                    waiting_filter = getattr(task, "waiting_for_filter", "")
                    time_work = getattr(task, "time_work", "")
                    time_setup = getattr(task, "time_setup", "")

                    formatted_output.append(
                        f"    Заказ: {task.order.account_number}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup}, Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
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

    # filters_json = 'Оборудование/Фильеры.json'
    # # Чтение JSON-файла в массив
    # with open(filters_json, 'r', encoding='utf-8') as file:
    #     filters_array = json.load(file)

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

    equipment_types = list(ind['wiredrawing'].keys())

    # # Убираем ThreadPoolExecutor и просто последовательно обрабатываем
    # for eq_type in equipment_types:
    #     time_total += calculate_setup_time_for_tasks(
    #         ind['wiredrawing'][eq_type],
    #         filters_dict,
    #         eq_type,
    #         print_logs
    #     )

    # Параллельно запускаем расчёты для каждого оборудования
    with ThreadPoolExecutor(max_workers=3) as executor: # Работает только с ThreadPoolExecutor
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
            order.equipment.capacity = settings.get("REMAINING_BASKET_LENGTH", order.equipment.remaining_basket_length)
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
                    filters_dict[filter_diameter] = {"ВремяОкончанияРаботы": today_midnight,
                                                     "ИспользуетсяОборудованием": "", "ИспользуетсяЗаказом": ""}
                    # print(f"Добавлена фильера с диаметром {filter_diameter}")


# Функция для установки времени начала и конца заказа
def setup_time_begin_end(tasks):
    for i in range(len(tasks)):
        tasks[i].time_begin = tasks[i - 1].time_ending + timedelta(
            minutes=tasks[i].time_setup)  # Время начала заказа - время конца предыдущего заказа + время перенастройки
        tasks[i].time_ending = tasks[i].time_begin + timedelta(
            minutes=tasks[i].time_work)  # Время конца заказа - время начала текущего заказа + время в работе
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
                    awaiting_filters = list(filters_time.keys())[
                        list(filters_time.values()).index(tasks[i].time_penalty)]  # Диаметр ожидаемой фильеры
                    tasks[i].waiting_for_equipment = filters_dict[awaiting_filters][
                        'ИспользуетсяОборудованием']  # Пишем на каком оборудовании фильера, которая нам нужна
                    tasks[i].waiting_for_order = filters_dict[awaiting_filters][
                        'ИспользуетсяЗаказом']  # Пишем какой заказ занимает нашу фильеру
                    tasks[i].waiting_for_filter = str(awaiting_filters)  # Пишем какую фильеру ждет заказ

                for filters in filters_in_use:
                    filters_dict[filters]['ВремяОкончанияРаботы'] = tasks[i].time_ending + timedelta(
                        minutes=tasks[i].time_penalty)  # Фильера освободиться через время окончания заказа + штраф

        general_penalty += tasks[i].time_penalty  # Общий штраф всей очереди

    if not tasks:
        print("tasks[] - пустой ")
        return 0
    else:
        return ((tasks[-1].time_ending - tasks[
            0].time_ending).total_seconds() / 60) + general_penalty  # Общее время = Время от начала первого до конца последнего + сумма всех штрафов


def get_cost_basket(tasks_with_basket, baskets):
    total_time = 0  # суммарное время перенастроек
    downtime = 0  # время простоев волочилки
    uptime = 0  # время простоев мультика
    time_route_to_basket = 0  # время между корзинами на волочилке
    if len(baskets) == 0:
        return 0
    # baskets = [task for task in tasks_with_basket if isinstance(task, str)]
    routes = get_routes(tasks_with_basket, baskets)

    # reserve_time = baskets[0].time_on_multivare
    # num_task = len(tasks_with_basket) - len(baskets)

    time_baskets = copy.copy([basket.time_on_multivare for basket in baskets])
    time_routes = copy.copy([get_time_route(route) for route in routes])

    for i, time_ in enumerate(time_baskets):
        t_time_drawing = time_routes[i] - time_
        if t_time_drawing < 0:
            downtime += -t_time_drawing
        else:
            try:
                t_time_multik = time_baskets[i + 1] - t_time_drawing
                # Для первой корзины не сможем посчитать простой мультика, т.к. есть еще время из запаса второй корзины
                if i:
                    if t_time_multik < 0:
                        uptime = t_time_multik
                else:
                    time_baskets[i + 1] -= t_time_multik
            except IndexError:
                continue

        # Если корзина будет последней, чтобы не было ошибок
        try:
            time_routes[i + 1] += WireDrawingMachine.W
        except IndexError:
            continue

    return sum(time_routes) + downtime * 1.5 + uptime * 1.5


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


def get_time_route(tasks: [WireDrawingTask]):
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
    # time += (WireDrawingMachine.W if number_route else 0)

    return time


def run():
    return run_genetic_algorithm()
