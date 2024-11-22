import numpy
from deap import base, creator, tools, algorithms
import random

import Equipments
from Tasks import Task, TaskMeta
from Equipments import MultivareMachine, WireDrawingMachine, Equipment


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


# Основная функция запуска алгоритма
def run_genetic_algorithm(tasks, pop_size=50, cxpb=0.7, mutpb=0.2, ngen=50):

    # константы задачи
    HALL_OF_FAME_SIZE = len(tasks) * 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = len(tasks) * 200  # количество индивидуумов в популяции
    MAX_GENERATIONS = len(tasks)  # максимальное количество поколений
    P_CROSSOVER = 1  # вероятность скрещивания
    P_MUTATION = 0  # вероятность мутации индивидуума

    toolbox = base.Toolbox()

    # Настройка среды DEAP для минимизации времени
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", dict, fitness=creator.FitnessMin)

    toolbox.register("individual", tools.initIterate, creator.Individual, lambda: generate_individual())
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("randomOrder", random.sample, range(len(tasks)), len(tasks))
    toolbox.register("individualCreator", tools.initIterate, creator.Individual, toolbox.randomOrder)
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)

    population = toolbox.population(n=POPULATION_SIZE)

    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", tools.cxUniform, indpb=0.5)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
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

    # Выбираем рандомное оборудование на задание из подходящих оборудований
    Task.assign_tasks_to_equipment(TaskMeta.get_instances_all())

    # задание на каждый тип оборудований
    individual = {}
    for eq in Equipment.get_all_instances():
        for type in eq.equipment_type:
            if individual.get(type, None) is None:
                individual[type] = {}
            individual[type][eq.equipment_name] = TaskMeta.get_instances_by_type(equipment=eq)

    return individual


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def evaluate_fitness(individual):
    multivare_time = sum(task.time_work for task in individual['multivare'])
    wiredrawing_time = sum(task.time_work for task in individual['wiredrawing'])
    return multivare_time + wiredrawing_time,


def run(tasks):
    run_genetic_algorithm(tasks)
