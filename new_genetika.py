import time
from datetime import datetime
from pickle import GLOBAL

import numpy
from deap import base, creator, tools, algorithms
import random
import copy

from numpy.random.mtrand import choice

import Equipments
import Tasks
from Tasks import Task, TaskMeta, MultivareTask, WireDrawingTask, Basket
from Equipments import MultivareMachine, WireDrawingMachine, Equipment

TASKS = []


def varAnd(population, toolbox, cxpb, mutpb):
    offspring = [toolbox.clone(ind) for ind in population]

    # Apply crossover and mutation on the offspring
    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            toolbox.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values  # Удаление старого значения fitness
            del offspring[i].fitness.values  # Удаление старого значения fitness

    for i in range(len(offspring)):
        for equipment_type in offspring[i].keys():
            for equipment in offspring[i][equipment_type]:
                tools.mutShuffleIndexes(
                    offspring[i][equipment_type][equipment], indpb=1.0 / len(offspring[i][equipment_type][equipment])
                    )
        del offspring[i].fitness.values

    return offspring


def eaSimpleWithElitism(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=__debug__):
    """This algorithm is similar to DEAP eaSimple() algorithm, with the modification that
    halloffame is used to implement an elitism mechanism. The individuals contained in the
    halloffame are directly injected into the next generation and are not subject to the
    genetic operators of selection, crossover and mutation.
    """
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is None:
        raise ValueError("halloffame parameter must not be empty!")

    halloffame.update(population)
    hof_size = len(halloffame.items) if halloffame.items else 0

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # Begin the generational process
    for gen in range(1, ngen + 1):

        # Select the next generation individuals
        offspring = toolbox.select(population, len(population) - hof_size)

        # Vary the pool of individuals
        if isinstance(offspring[0], dict):
            offspring = varAnd(offspring, toolbox, cxpb, mutpb)
        else:
            offspring = algorithms.varAnd(offspring, toolbox, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # add the best back to population:
        offspring.extend(halloffame.items)

        # Update the hall of fame with the generated individuals
        halloffame.update(offspring)

        # Replace the current population by the offspring
        population[:] = offspring

        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

    return population, logbook


def mutate(individual, mutation_rate=0.05):
    """Кастомная мутация для индивидов."""
    # Проходим по каждому типу оборудования
    for equipment in individual.keys():
        # Проверяем, следует ли мутировать текущее задание
        if random.random() < mutation_rate:
            # Перемешиваем список заданий на данном оборудовании
            random.shuffle(individual[equipment])

    return individual


def convert_tasks_to_indices(tasks, all_tasks):
    """
    Конвертирует список заданий в индексы, основываясь на всем списке задач.
    """
    return [all_tasks.index(task) for task in tasks]


def convert_indices_to_tasks(indices, all_tasks):
    """
    Конвертирует список индексов обратно в задачи.
    """
    return [all_tasks[i] for i in indices]


def cxOrderedCustom(ind1, ind2):
    """
    Кастомный оператор скрещивания на основе cxOrdered для сложной структуры.
    """

    # Создаем копии родителей для потомков
    # child1, child2 = copy.deepcopy(ind1), copy.deepcopy(ind2)
    child1, child2 = {}, {}

    for equipment_type in ind1.keys():

        # Перебираем каждое оборудование
        for equipment in ind1[equipment_type]:
            tasks_ind1 = ind1[equipment_type][equipment]
            tasks_ind2 = ind2[equipment_type][equipment]
            # Проверяем, есть ли задания для текущего оборудования
            if len(tasks_ind1) < 2 or len(tasks_ind2) < 2:
                # Нет смысла применять скрещивание, если недостаточно заданий для скрещивания
                continue
            # Конвертируем задания в индексы
            indices1 = list(range(len(tasks_ind1)))
            indices2 = list(range(len(tasks_ind2)))

            # Применяем стандартный cxOrdered на индексы
            tools.cxUniformPartialyMatched(indices1, indices2, indpb=2.0 / 150)

            # Конвертируем индексы обратно в задания
            child1[equipment] = [copy.deepcopy(tasks_ind1[i]) for i in indices1]
            child2[equipment] = [copy.deepcopy(tasks_ind2[i]) for i in indices2]

    return child1, child2

# Основная функция запуска алгоритма
def run_genetic_algorithm(pop_size=50, cxpb=0.7, mutpb=0.2, ngen=50):
    TASKS = Task.get_instances_all()
    # константы задачи
    HALL_OF_FAME_SIZE = len(TASKS) * 0.1  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = len(TASKS)   # количество индивидуумов в популяции
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

    TaskMeta.get_instances_by_type(equipment_type='multivare')
    TaskMeta.get_instances_by_type(equipment_type='wiredrawing')

    # задание на каждый тип оборудований
    individual = {}
    for eq in Equipment.get_all_instances():
        for equipment_type in eq.equipment_type:
            if individual.get(equipment_type, None) is None:
                individual[equipment_type] = {}
            task_c = copy.deepcopy(TaskMeta.get_instances_by_type(equipment=eq))
            individual[equipment_type][eq.equipment_name] = random.sample(task_c, len(task_c))

    for eq in individual['multivare']:
        task_m = copy.deepcopy(individual['multivare'][eq])
        MultivareTask.calculate_setup_time_all(individual['multivare'][eq])
        calculating_basket(individual, task_m)

    for eq in individual['wiredrawing']:
        task_w = individual['wiredrawing'][eq]
        random.shuffle(task_w)
        WireDrawingTask.calculate_setup_time_all(task_w)
    time_end = datetime.now()
    print(time_end - time_start)
    return individual


def get_task_indices(tasks, task_c):
    return list(next(i for i, task2 in enumerate(tasks) if task2.order.UUID == task1.order.UUID) for task1 in task_c)


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def get_cost_multivare(ind):
    time = 0
    # map(lambda x: x.capacity * 0 + 8, Equipment.get_instances_by_type(equipment_type='multivare'))
    for eq in ind['multivare']:
        tasks = copy.deepcopy(ind['multivare'][eq])
        for task in tasks:
            time += task.time_setup

    return time


def calculating_basket(ind, task):
    """
    Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
    если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
    :return:
    """

    temp_basket: Basket = copy.deepcopy(Basket(None))
    for order in task:
        if order.equipment.capacity - order.num_basket >= 0:
            temp_basket.append(order, order.num_basket)
            order.equipment.capacity -= order.num_basket  # сколько нужно до 8 корзин
            # Если со следующим заказом получается меньше 8 корзин, но он занимает сам по себе больше 8 корзин
        else:
            temp_basket.append(order, order.equipment.capacity)

            Task.assign_tasks_to_equipment(temp_basket)
            ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name].append(temp_basket)

            num_basket = order.num_basket - order.equipment.capacity
            while num_basket > 8:
                b = copy.deepcopy(Basket(order, 8))
                Task.assign_tasks_to_equipment(b)
                ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name].append(b)
                num_basket -= 8

            order.equipment.capacity = 8 - num_basket
            temp_basket = copy.deepcopy(Basket(order, num_basket))
    else:
        if len(temp_basket.orders) > 0:
            Task.assign_tasks_to_equipment(temp_basket)
            ind[temp_basket.equipment_type][temp_basket.equipment.equipment_name].append(temp_basket)


def get_cost_drawing(ind):
    time = 0
    # return 0
    # indexes_baskets = individual.basket
    total_time = 0  # суммарное время перенастроек
    num_downtime = 0  # количество простоев волочилки
    num_uptime = 0  # количесвто простоев мультика
    time_route_to_basket = 0

    for eq in ind['wiredrawing']:
        tasks = ind['wiredrawing'][eq]
        if not any(isinstance(task, Basket) for task in tasks):
            for task in tasks:
                time += task.time_setup
        else:
            time += get_cost_new(tasks)

    return time


def get_cost_new(tasks_with_basket):

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
            continue

        if reserve_time < time_route_to_basket < reserve_time + baskets[route + 1].time_work:
            reserve_time = baskets[route + 1].time_work - (time_route_to_basket - reserve_time)
            if reserve_time < WireDrawingMachine.W:
                num_downtime += 1
        elif time_route_to_basket < reserve_time:
            num_downtime += 1
            reserve_time = baskets[route + 1].time_work
        elif time_route_to_basket > reserve_time + baskets[route + 1].time_work - WireDrawingMachine.W:
            num_uptime += 1
            reserve_time = baskets[route + 1].time_work

        # total_time += time_route_to_basket
        time_route_to_basket = 0

    else:

        time_route_to_basket += get_time_route(routes[-2], routes.index(routes[-2]))

        reserve_time = baskets[-1].time_work

        if reserve_time < time_route_to_basket < reserve_time + baskets[-1].time_work:
            pass
        elif time_route_to_basket < reserve_time:
            num_downtime += 1
        elif time_route_to_basket > reserve_time:
            num_uptime += 1

    return total_time + (20000 * num_downtime) + (20000 * num_uptime)


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
