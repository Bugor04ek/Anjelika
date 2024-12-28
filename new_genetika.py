from Tasks import Task, TaskMeta, Basket, MultivareTask, WireDrawingTask, WireDrawingMachine
import json
import os
from datetime import datetime, timedelta
from Equipments import Equipment
import random
import copy
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from itertools import permutations
from collections.abc import Iterable
from tqdm import tqdm
import time

TASKS = []
settings = None
filters_array = []


# Получение настроек для ГА
def load_settings():
    global settings
    # Путь к файлу настроек
    settings_path = os.path.join("Shared", "settings.json")

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
        with open(settings_path, "w", encoding="utf-8") as file:  # noinspection PyTypeChecker
            json.dump(default_settings, file, indent=4, ensure_ascii=False)
        print(f"Файл настроек не найден. Создан файл с дефолтными значениями: {settings_path}")
        return default_settings

    # Если файл существует, загружаем настройки из него
    with open(settings_path, "r", encoding="utf-8") as file:
        settings = json.load(file)

    return settings


# Получение значений фильер для ГА
def get_filters():
    filters_json = 'res_Equipments/Фильеры.json'
    # Чтение JSON-файла в массив
    with open(filters_json, 'r', encoding='utf-8') as file:
        return json.load(file)


def generate_individual(tasks):
    """Создает индивида с распределением задач по оборудованию."""

    time_start = datetime.now()
    Task.assign_tasks_to_equipment(tasks)

    # задание на каждый тип оборудований
    individual = {}

    all_instances_eq = Equipment.get_all_instances()

    # Предварительная фильтрация задач для оборудования
    all_tasks_by_equipment = {eq: TaskMeta.get_instances_by_type(equipment=eq) for eq in all_instances_eq}

    for eq in all_instances_eq:
        task_c = copy.deepcopy(all_tasks_by_equipment[eq])
        random.shuffle(task_c)  # Быстрее, чем random.sample
        for equipment_type in eq.equipment_type:
            individual.setdefault(equipment_type, {})
            individual[equipment_type][eq.equipment_name] = task_c

    individual['Basket'] = calculating_basket(individual)

    for basket in individual['Basket']:
        ind = individual[basket.equipment_type][basket.equipment.equipment_name]
        ind.insert(random.randint(0, len(ind)), basket)

    time_end = datetime.now()
    # print(f"Время выполнения generate_individual: {time_end - time_start}")
    return individual


def generate_population(tasks, population_size):
    """Создает начальную популяцию индивидов."""
    population = [generate_individual(tasks) for _ in
                  tqdm(range(population_size), desc="Initial population", ncols=100)]
    return population


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def get_cost_multivare(ind):
    time_total = 0
    for eq in ind['multivare']:
        tasks = ind['multivare'][eq]
        # MultivareTask.calculate_setup_time_all(tasks)
        # Предположим, что задачи можно представить как NumPy массивы
        time_setup_array = np.array([task.time_setup for task in tasks])

        # Можно объединить все вычисления в одну строку, если есть возможность
        time_total += np.sum(time_setup_array)

    return time_total


def calculating_basket(ind):
    """
    Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
    если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
    :return:
    """

    updated_baskets = []

    for eq, task_m in ind['multivare'].items():
        # Обновляем вместимость оборудования
        for order in task_m:
            order.equipment.capacity = settings.get("REMAINING_BASKET_LENGTH", order.equipment.remaining_basket_length)

        # Расчет времени перенастройки для всех заданий
        MultivareTask.calculate_setup_time_all(task_m)

        temp_basket: Basket = Basket(None)

        for order in task_m:
            remaining_capacity = order.equipment.capacity - order.num_basket

            if remaining_capacity >= 0:
                # Если текущий заказ помещается в оставшуюся вместимость
                temp_basket.append(order, order.num_basket)
                order.equipment.capacity -= order.num_basket
            else:
                # Если не помещается
                temp_basket.append(order, order.equipment.capacity)
                updated_baskets.append(temp_basket)

                num_basket = order.num_basket - order.equipment.capacity
                # Обработка корзин, если есть остатки
                while num_basket > 8:
                    temp_basket = Basket(order, 8)
                    updated_baskets.append(temp_basket)
                    num_basket -= 8

                # Обновляем оставшуюся вместимость
                order.equipment.capacity = 8 - num_basket
                temp_basket = Basket(order, num_basket)

        if temp_basket.orders:
            updated_baskets.append(temp_basket)

    return updated_baskets


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
    total_time = 0
    # loop over all indices in the list:
    for i, task in enumerate(tasks):

        # index is part of the current route:
        if not isinstance(task, Basket):
            route.append(task)
            total_time = task.time_setup + task.time_work
        # separator index - route is complete:
        else:
            baskets[b].time_prev_group_orders = total_time
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

    times_work = np.array([task.time_work for task in tasks])
    times_setup = np.array([task.time_setup for task in tasks])
    return np.sum(times_work + times_setup)


def get_cost_basket(tasks_with_basket, baskets):
    if len(baskets) == 0:
        return 0

    # Разбиваем задачи на маршруты
    routes = get_routes(tasks_with_basket, baskets)

    # Время на мультиваре и маршрутах
    time_baskets = np.array([basket.time_on_multivare for basket in baskets])
    time_routes = np.array([get_time_route(route) for route in routes])

    downtime = 0  # время простоев волочилки
    uptime = 0  # время простоев мультика

    # Цикл по корзинам
    for i in range(len(baskets)):
        t_time_drawing = time_routes[i] - time_baskets[i]

        if t_time_drawing < 0:
            downtime += -t_time_drawing
            baskets[i].downtime = downtime
        else:
            if i < len(baskets) - 1:  # Проверяем наличие следующей корзины
                t_time_multik = time_baskets[i + 1] - t_time_drawing
                if i > 0 and t_time_multik < 0:
                    uptime += -t_time_multik
                    baskets[i].uptime = uptime
                elif i > 0:
                    time_baskets[i + 1] -= max(0, t_time_multik)

        if i < len(baskets) - 1:
            time_routes[i + 1] += WireDrawingMachine.W

    # Итоговая стоимость
    return np.sum(time_routes) + downtime + uptime


def add_missing_filters(filters_dict, ind):
    # Получаем сегодняшний день в 0:00
    today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Преобразуем ключи filters_dict в set для ускорения проверки наличия
    existing_filters = set(filters_dict.keys())

    def flatten(obj):
        """Разворачивает вложенные списки в плоский список."""
        for i in obj:
            if isinstance(i, Iterable) and not isinstance(i, (str, bytes)):
                yield from flatten(i)
            else:
                yield i

    for eq, tasks in ind.items():
        for task in tasks:
            spin_road = task.spin_road

            # Универсально преобразуем spin_road в плоский список
            if isinstance(spin_road, list):
                spin_road = list(flatten(spin_road))
            else:
                spin_road = [spin_road]

            # Преобразуем в numpy массив и фильтруем элементы, равные 0
            spin_road = np.array(spin_road)
            spin_road = spin_road[spin_road != 0]  # Фильтруем нулевые элементы

            # Проверяем и добавляем отсутствующие фильеры
            for filter_diameter in spin_road:
                if filter_diameter not in existing_filters:
                    # Добавляем фильеру с минимальными параметрами
                    filters_dict[float(filter_diameter)] = {
                        "ВремяОкончанияРаботы": today_midnight,
                        "ИспользуетсяОборудованием": "",
                        "ИспользуетсяЗаказом": "",
                    }
                    existing_filters.add(filter_diameter)  # Обновляем множество ключей
            spin_road = spin_road.tolist()


# Функция для установки времени начала и конца заказа
def setup_time_begin_end(tasks):
    # Обработка первой задачи отдельно
    tasks[0].time_begin = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # Начало первой задачи
    tasks[0].time_ending = tasks[0].time_begin + timedelta(minutes=tasks[0].time_work)

    # Итерация по задачам начиная со второй
    for i in range(1, len(tasks)):  # Начинаем с 1, чтобы избежать ошибки для первой задачи
        tasks[i].time_begin = tasks[i - 1].time_ending + timedelta(
            minutes=tasks[i].time_setup)  # Время начала заказа - время конца предыдущего заказа + время перенастройки
        tasks[i].time_ending = tasks[i].time_begin + timedelta(
            minutes=tasks[i].time_work)  # Время конца заказа - время начала текущего заказа + время в работе

    return tasks


def calculate_setup_time_for_tasks(tasks, filters_dict, eq_type, print_logs=False):
    """Вычисление времени переналадки на одном оборудовании с учётом фильер."""
    general_penalty = 0
    empty_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Обработка всех задач
    for task in tasks:
        all_free = True
        filters_in_use = {}

        # Проверка spin_road на старом и новом оборудовании
        # spins =  task.spin_road if task.equipment.equipment_name == "old" else [task.spin_road]
        road = task.spin_road

        # Проверяем, является ли это список списков
        if isinstance(road, list) and all(isinstance(item, list) for item in road):
            road = road[0]  # Ничего не делаем
        elif isinstance(road, list):  # Просто список
            pass

        for spin in road:
            if spin == 0: continue

            # Проверяем, занята ли фильера
            if filters_dict[spin]['ВремяОкончанияРаботы'] != empty_time:
                all_free = False
                filters_in_use[spin] = filters_dict[spin]['ВремяОкончанияРаботы']

        if all_free:
            for spin in road:
                if spin == 0: continue
                filters_dict[spin]['ВремяОкончанияРаботы'] += timedelta(minutes=task.time_work)
                filters_dict[spin]['ИспользуетсяОборудованием'] = task.equipment.equipment_name
                filters_dict[spin]['ИспользуетсяЗаказом'] = "Корзина" if isinstance(task,
                                                                                    Basket) else task.account_number
        else:
            # Рассчитываем время ожидания для занятой фильеры
            filters_time = {
                filter_: (filters_dict[filter_]['ВремяОкончанияРаботы'] - task.time_begin).total_seconds() / 60
                for filter_ in filters_in_use
            }

            # Если требуется ожидание, то вычисляем максимальный штраф
            max_penalty = max(filters_time.values(), default=0)
            if max_penalty > 0:
                task.time_penalty = max_penalty
                waiting_filter = max(filters_time, key=filters_time.get)
                task.waiting_for_equipment = filters_dict[waiting_filter]['ИспользуетсяОборудованием']
                task.waiting_for_order = filters_dict[waiting_filter]['ИспользуетсяЗаказом']
                task.waiting_for_filter = str(waiting_filter)

            # Обновляем время окончания для занятых фильер
            for filter_ in filters_in_use:
                filters_dict[filter_]['ВремяОкончанияРаботы'] = task.time_ending + timedelta(minutes=task.time_penalty)

    # Суммируем общий штраф
    general_penalty += task.time_penalty

    # Возвращаем итоговое время переналадки + общий штраф
    if tasks:
        return ((tasks[-1].time_ending - tasks[0].time_ending).total_seconds() / 60) + general_penalty
    return 0


def get_cost_drawing(ind, print_logs=False):
    time_total = 0

    # Получаем сегодняшний день в 0:00
    today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Создаем словарь фильеров
    filters_dict = {
        item['Диаметр']: {
            "ВремяОкончанияРаботы": today_midnight,
            "ИспользуетсяОборудованием": "",
            "ИспользуетсяЗаказом": ""
        }
        for item in filters_array
    }

    # Добавляем недостающие фильеры из задач
    add_missing_filters(filters_dict, ind['wiredrawing'])
    filters_dict = dict(sorted(filters_dict.items()))

    for eq, tasks in ind['wiredrawing'].items():
        # Рассчитываем время перенастройки
        WireDrawingTask.calculate_setup_time_all(tasks)
        if any(isinstance(task, Basket) for task in tasks):
            time_total += get_cost_basket(tasks, ind['Basket'])
        else:
            time_total += sum(task.time_setup for task in tasks)

        # Рассчитываем время начала и окончания
        setup_time_begin_end(tasks)

        # Добавляем затраты времени на обработку фильеров
        # time_total += calculate_setup_time_for_tasks(tasks, filters_dict, eq, print_logs)

    time_total += time_with_filters(ind['wiredrawing'], filters_dict)

    return time_total


def time_with_filters(ind, filters_dict):
    # time_total = 0

    names = list(ind.keys())  # Получаем список названий
    # random.shuffle(names) # Делаем так что бы все время начало было с разных оборудований
    num_of_stage = max(len(ind[eq]) for eq in names)

    general_penalty = 0

    for i in range(num_of_stage):
        for eq in names:
            if i < len(ind[eq]):

                filters_in_use = {}
                awaiting_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                if isinstance(ind[eq][i].spin_road, list) and isinstance(ind[eq][i].spin_road[0], list):
                    current_spins = random.choice(ind[eq][i].spin_road)
                else:
                    current_spins = ind[eq][i].spin_road

                # Определяем какие из фильер в работе
                for spin in current_spins:
                    if spin == 0: continue

                    if filters_dict[spin]['ИспользуетсяЗаказом'] != "":
                        filters_in_use[spin] = {"ВремяОкончанияРаботы": filters_dict[spin]['ВремяОкончанияРаботы']}

                # Определяем время самой долгой фильеры. Что бы начать делать наш заказ, надо ждать её
                if filters_in_use:
                    max_key = max(filters_in_use, key=lambda k: filters_in_use[k]["ВремяОкончанияРаботы"])
                    awaiting_time = filters_dict[max_key]['ВремяОкончанияРаботы']
                    ind[eq][i].time_penalty = max(0, ((awaiting_time - ind[eq][i].time_ending).total_seconds()) / 60)
                    if ind[eq][i].time_penalty > 0:
                        ind[eq][i].waiting_for_filter = max_key
                        ind[eq][i].waiting_for_equipment = filters_dict[max_key]['ИспользуетсяОборудованием']
                        ind[eq][i].waiting_for_order = filters_dict[max_key]['ИспользуетсяЗаказом']
                        general_penalty += ind[eq][i].time_penalty

                for spin in current_spins:
                    if spin == 0: continue
                    filters_dict[spin]['ВремяОкончанияРаботы'] = ind[eq][i].time_ending + timedelta(
                        minutes=(ind[eq][i].time_penalty))
                    filters_dict[spin]['ИспользуетсяОборудованием'] = eq

                    if isinstance(ind[eq][i], Basket):
                        filters_dict[spin]['ИспользуетсяЗаказом'] = "Корзина"
                    else:
                        filters_dict[spin]['ИспользуетсяЗаказом'] = ind[eq][i].account_number

                #print(f"Этап: {i}, Оборудование: {eq}, Фильтр: {spin}, Время работы: {filters_dict[spin]['ВремяОкончанияРаботы']}")

            else:
                pass

    return general_penalty


def fitness_function(individual):
    multivare_time = get_cost_multivare(individual)
    drawing_time = get_cost_drawing(individual)
    return multivare_time + drawing_time


#------------------------------------------------------------------

def run_genetic_algorithm():
    time_start = datetime.now()

    # Параметры ГА
    population_size = 1000  # Размер популяции
    num_generations = 20  # Число поколений
    elitism_rate = 0.2  # Доля элитных особей, сохраняемых в следующем поколении
    mutation_probability = 0.1
    num_elites = round(population_size * elitism_rate)

    # Генерация начальной популяции
    population = generate_population(TaskMeta.get_instances_all(), population_size)
    fitness_values = [fitness_function(individual) for individual in population]

    best_initial_individual = min(population, key=fitness_function)
    best_initial_fitness = fitness_function(best_initial_individual)
    tqdm.write(f"Best Fitness = {best_initial_fitness}")
    time.sleep(0.5)  # Имитация работы

    for generation in tqdm(range(num_generations), desc="Generations", ncols=100):

        # Находим элитные особи
        elites = elitism_selection(population, fitness_values, num_elites)

        # Создаем потомков
        offspring = mate(elites, population_size)

        # Применяем мутацию к потомкам
        offspring = [mutate(individual, mutation_probability) for individual in offspring]

        # Формируем новую популяцию
        population = elites + offspring

        # Оценка текущей популяции
        fitness_values = [fitness_function(individual) for individual in population]

        best_individual = min(population, key=fitness_function)  # Для задачи минимизации

        # Выводим статистику последнего поколения
        if generation == num_generations - 1:
            for eq, tasks in best_individual['wiredrawing'].items():
                for taks in tasks:
                    taks.waiting_for_equipment = ""
                    taks.waiting_for_order = ""
                    taks.waiting_for_filter = 0

    time_end = datetime.now()
    for eq, tasks in best_individual['wiredrawing'].items():
        tasks[0].comment_setup = ""
        #WireDrawingTask.calculate_setup_time_all(tasks)

    print(f"Время выполнения (размер популяции: {population_size}): {time_end - time_start}")
    best_fitness = fitness_function(best_individual)
    print(f"Generation {generation}: Best Fitness = {best_fitness}\n")
    print(f"{round(best_initial_fitness)} --> {round(best_fitness)}\n")

    # Возвращаем лучшего индивида
    formatted_solution = format_best_solution(best_individual)
    print(formatted_solution)
    return best_individual


#------------------------------------------------------------------

def format_best_solution(best_order):
    """Форматирует вывод для лучшего решения."""
    formatted_output = []

    for equipment_type, equipment_data in best_order.items():
        if (equipment_type == "Basket"): continue
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
                        f"    Время работы группы заказов: {total_time}, Время работы заказов на мультике: {time_on_multivare}\n"
                        f"    Корзина (длина: {task.sum_basket}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup},  Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
                        f"Маршрут фильер: {spin_road}, Комментарий к перенастройке: {comment_setup}"
                    )

                    # formatted_output.append(basket_details)
                    for basket_task in task.orders:
                        Name = getattr(basket_task, "account_number", "")
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
                            f"      Заказ: {Name}, Диаметр: {diameter}"
                            # f"        Заказ: {Name}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup}, Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
                            # f"Маршрут фильер: {spin_road}, Комментарий к перенастройке: {comment_setup}"
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
                        f"    Заказ: {task.account_number}, Диаметр: {diameter}, Время работы: {time_work}, Время перенастройки: {time_setup}, Штраф за ожидание: {penalty}, Ожидает Фильеру: {waiting_filter}, На оборудовании: {waiting_equipment}, В заказе: {waiting_order} "
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


def elitism_selection(population, fitness_values, num_elites):
    """Выбирает элитных особей, сортируя популяцию по фитнесу."""
    sorted_population = sorted(zip(population, fitness_values), key=lambda x: x[1])  # Для задачи минимизации
    elites = [ind for ind, _ in sorted_population[:num_elites]]
    return elites


def mutate(individual, indpb):
    """
    Выполняет мутацию особи путем случайной перетасовки элементов списка
    для каждого оборудования с вероятностью indpb.
    """
    for equipment_type in individual.keys():
        if equipment_type == 'Basket': continue
        for equipment in individual[equipment_type]:
            # Генерируем случайное число для принятия решения о мутации
            if random.random() < indpb:
                # Перетасовка элементов списка
                random.shuffle(individual[equipment_type][equipment])

    individual['Basket'] = calculating_basket(individual)
    return individual


def mate(elites, population_size):
    offspring = []  # Список для хранения потомков

    for ind1 in elites:
        for _ in range(round((population_size - len(elites)) / len(elites)) - 1):

            # Создаем копии родителей для потомков
            child1 = copy.deepcopy(ind1)

            for equipment_type in child1.keys():
                if equipment_type == 'Basket':
                    for _ in range(2):
                        for basket in child1['Basket']:
                            i = child1['wiredrawing'][basket.equipment.equipment_name].index(basket)
                            if i != len(child1['wiredrawing'][basket.equipment.equipment_name]) - 1 and basket.downtime > 0:
                                child1['wiredrawing'][basket.equipment.equipment_name].remove(basket)
                                child1['wiredrawing'][basket.equipment.equipment_name].insert(i+1, basket)
                            elif basket.uptime > 0:
                                child1['wiredrawing'][basket.equipment.equipment_name].remove(basket)
                                child1['wiredrawing'][basket.equipment.equipment_name].insert(i - 1, basket)
                    else:
                        continue
                for equipment in child1[equipment_type]:
                    tasks_ind1 = child1[equipment_type][equipment]

                    if len(tasks_ind1) < 2:
                        continue

                    t_tasks = np.random.choice(tasks_ind1, size=4 if len(tasks_ind1) > 4 else 1, replace=False)
                    for t_task in t_tasks:
                        if isinstance(t_task, Basket):
                            continue
                        best_num_group = {}
                        for eq in t_task.acceptable_equipment:
                            if equipment_type == 'multivare':
                                best_num_group[eq] = [child1[equipment_type][eq.equipment_name].index(task) for task in
                                                      child1[equipment_type][eq.equipment_name] if
                                                      task.spin_road[0] == t_task.spin_road[0]]
                            elif equipment_type == 'wiredrawing':
                                best_num_group[eq] = [child1[equipment_type][eq.equipment_name].index(task) for task in
                                                      child1[equipment_type][eq.equipment_name] if
                                                      task.voloka == t_task.voloka]

                        best_eq = sorted(best_num_group.items(), key=lambda x: len(x[1]), reverse=True)[0][0]
                        if best_eq.equipment_name != equipment:
                            WireDrawingTask.assign_tasks_to_equipment(t_task, best_eq)

                        child1[equipment_type][equipment].remove(t_task)
                        child1[equipment_type][best_eq.equipment_name].insert(best_num_group[best_eq][0], t_task)

            child1['Basket'] = calculating_basket(child1)
            offspring.append(child1)

    while len(offspring) < round((population_size - len(elites))):
        child_с = copy.deepcopy(random.choice(elites))
        offspring.append(mutate(child_с, 1))

    return offspring[:(population_size - len(elites))]


def run():
    # Загрузка настроек из JSON-файла
    global settings
    global filters_array
    settings = load_settings()
    filters_array = get_filters()
    # мб заполнить словарь фильер тут через getallinstace()

    return run_genetic_algorithm()
