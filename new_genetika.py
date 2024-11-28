import numpy
from deap import base, creator, tools, algorithms
import random
import copy

from numpy.random.mtrand import choice

import Equipments
import Tasks
from Tasks import Task, TaskMeta, MultivareTask, WireDrawingTask, Basket
from Equipments import MultivareMachine, WireDrawingMachine, Equipment


def varAnd(population, toolbox, cxpb, mutpb):
    offspring = [toolbox.clone(ind) for ind in population]

    # Apply crossover and mutation on the offspring
    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            toolbox.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values  # Удаление старого значения fitness
            del offspring[i].fitness.values  # Удаление старого значения fitness
            offspring[i - 1].basket = []  # Удаление старого значения fitness
            offspring[i].basket = []  # Удаление старого значения fitness

    for i in range(len(offspring)):
        if random.random() < mutpb:
            offspring[i], = toolbox.mutate(offspring[i])
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


def uniform_crossover(tasks1, tasks2):
    """
    Унифицированный кроссовер для заданий одного типа оборудования.
    Выполняется с вероятностью indpb на уровне каждого задания.
    """
    child1, child2 = tasks1[:], tasks2[:]
    indpb = 0.5

    min_len = min(len(tasks1), len(tasks2))
    # Проходимся по каждому заданию в списках и случайно решаем, будем ли менять задание
    for i in range(min_len):
        if random.random() < indpb:
            # Меняем задания местами
            child1[i], child2[i] = child2[i], child1[i]

    return child1, child2


def mutate(individual):
    """Оператор мутации: случайное перемешивание задач на оборудовании."""
    for equipment_type in individual.keys():
        for equipment in individual[equipment_type]:
            # Получаем задачи для данного оборудования
            tasks = individual[equipment_type][equipment]

            # С вероятностью mutpb выполняем перемешивание задач
            if random.random() < 0.1:  # Вероятность мутации
                random.shuffle(tasks)

    # Возвращаем мутировавшего индивида в виде кортежа (так требует DEAP)
    return (individual,)


def crossover(parent1, parent2):
    """
    Кроссовер двух родителей для создания двух потомков.
    """
    # Копируем родителей, чтобы создать потомков
    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)

    for equipment_type in parent1.keys():
        # Получаем задания для каждого типа оборудования
        parent1_tasks = parent1[equipment_type]
        parent2_tasks = parent2[equipment_type]

        # Создаем новые списки для потомков
        child1_tasks = {}
        child2_tasks = {}

        # Проходим по каждому оборудованию внутри типа (например, old, new для wiredrawing)
        for equipment in parent1_tasks.keys():
            tasks1 = parent1_tasks[equipment]
            tasks2 = parent2_tasks[equipment]

            # Если у нас достаточно заданий для выполнения кроссовера
            if len(tasks1) > 1 and len(tasks2) > 1:
                # Выполняем унифицированный кроссовер внутри одного оборудования
                tasks1, tasks2 = uniform_crossover(tasks1, tasks2)

                # Обновляем потомков новыми заданиями
                child1_tasks[equipment] = tasks1
                child2_tasks[equipment] = tasks2

        # Обновляем задачи в потомках для текущего типа оборудования
        child1[equipment_type] = child1_tasks
        child2[equipment_type] = child2_tasks

    return child1, child2


# Основная функция запуска алгоритма
def run_genetic_algorithm(pop_size=50, cxpb=0.7, mutpb=0.2, ngen=50):
    # константы задачи
    HALL_OF_FAME_SIZE = 20  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = 100  # количество индивидуумов в популяции
    MAX_GENERATIONS = 10  # максимальное количество поколений
    P_CROSSOVER = 1  # вероятность скрещивания
    P_MUTATION = 0.05  # вероятность мутации индивидуума

    toolbox = base.Toolbox()

    # Настройка среды DEAP для минимизации времени
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Basket", list)
    creator.create("Individual", dict, fitness=creator.FitnessMin, basket=creator.Basket)

    toolbox.register("individualCreator", tools.initIterate, creator.Individual, generate_individual)
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)

    population = toolbox.populationCreator(n=POPULATION_SIZE)

    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", crossover)
    toolbox.register("mutate",  mutate)
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
    return population


# Создание начальной популяции на основе заданий
def generate_individual():
    """Создает индивида с распределением задач по оборудованию."""
    # Task_c = copy.deepcopy(Task)
    # TaskMeta_c = copy.deepcopy(TaskMeta)
    # Выбираем рандомное оборудование на задание из подходящих оборудований
    Task.assign_tasks_to_equipment(Task.get_instances_all())

    # задание на каждый тип оборудований
    individual = {}
    for eq in Equipment.get_all_instances():
        for equipment_type in eq.equipment_type:
            if individual.get(equipment_type, None) is None:
                individual[equipment_type] = {}
            task = TaskMeta.get_instances_by_type(equipment=eq)
            task_c = copy.deepcopy(task)
            individual[equipment_type][eq.equipment_name] = random.sample(task_c, len(task_c))

    return individual


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def get_cost_multivare(ind):
    time = 0
    for task in ind['multivare'].values():
        for i in range(1, len(task)):
            time += MultivareTask.calculate_setup_time(task[i], task[i - 1])

        calculating_basket(ind, task)

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
            ind.basket.append(temp_basket)
            # task_w = ind['wiredrawing'][temp_basket.equipment.equipment_name]
            # task_w.insert(random.randint(0, len(task)), temp_basket)

            order.equipment.remaining_basket_length -= 8
            num_basket = order.num_basket - order.equipment.capacity
            while num_basket > 8:

                b = copy.deepcopy(Basket(order, 8))
                Task.assign_tasks_to_equipment(b)
                ind.basket.append(b)
                # task_w = ind['wiredrawing'][temp_basket.equipment.equipment_name]
                # task_w.insert(random.randint(0, len(task_w)), b)

                order.equipment.remaining_basket_length -= 8
                num_basket -= 8

            order.equipment.capacity = 8 - num_basket
            temp_basket = copy.deepcopy(Basket(order, num_basket))
    else:
        if len(temp_basket.orders) > 0:
            Task.assign_tasks_to_equipment(temp_basket)
            ind.basket.append(temp_basket)
            # task_w = ind['wiredrawing'][temp_basket.equipment.equipment_name]
            # task_w.insert(random.randint(0, len(task_w)), temp_basket)
        order.equipment.capacity = 8


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
        for i in range(1, len(tasks)):
            time += WireDrawingTask.calculate_setup_time(tasks[i], tasks[i - 1])

    return time


def evaluate_fitness(individual):
    # eq = Equipment.get_all_instances()

    multivare_time = get_cost_multivare(individual)
    drawing_time = get_cost_drawing(individual)
    # for equipment_name in individual['multivare'].keys():
    #     multivare_time += sum(task.time_work for task in individual['multivare'][equipment_name])
    # for equipment_name in individual['wiredrawing'].keys():
    #     multivare_time += sum(task.time_work for task in individual['wiredrawing'][equipment_name])
    return multivare_time + drawing_time,


def run():
    run_genetic_algorithm()
