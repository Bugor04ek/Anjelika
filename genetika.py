import datetime
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import random
import matplotlib.pyplot as plt
import numpy

import consts
from consts import converting_indexes_to_numbers
from Оборудование.Multivare import *
from Оборудование.Dragger import *

# константы задачи
HALL_OF_FAME_SIZE = 500  # количеству индивидуумов, которых мы хотим хранить в зале славы

# константы генетического алгоритма
POPULATION_SIZE = 15000  # количество индивидуумов в популяции
P_CROSSOVER = 1  # вероятность скрещивания
P_MUTATION = 0  # вероятность мутации индивидуума
MAX_GENERATIONS = 70  # максимальное количество поколений


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


def main_multivare(orders: list[TaskForMultik]):
    start = datetime.datetime.now()

    len_orders = len(orders)

    # константы задачи
    HALL_OF_FAME_SIZE = len_orders * 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
    # константы генетического алгоритма
    POPULATION_SIZE = len_orders * 150  # количество индивидуумов в популяции
    # P_CROSSOVER = 1  # вероятность скрещивания
    # P_MUTATION = 0  # вероятность мутации индивидуума
    MAX_GENERATIONS = int(len_orders * 0.9)  # максимальное количество поколений

    time_on_dragger = QueueMultivare.form_matrix_multivare(orders)
    toolbox = base.Toolbox()

    df = pd.DataFrame(time_on_dragger)

    mode = "w" if os.path.exists("excel/matrix_time.xlsx") else "a"

    with ExcelWriter("excel/matrix_time.xlsx", mode=mode, engine="openpyxl") as writer:
        df.to_excel(writer)

    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # стратегия приспособления - минимальное время
    creator.create("Individual", list, typecode='i', fitness=creator.FitnessMin)  # представление индивидуумов
    toolbox.register("randomOrder", random.sample, range(len_orders), len_orders)
    toolbox.register("individualCreator", tools.initIterate, creator.Individual, toolbox.randomOrder)
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)
    toolbox.register("evaluate", QueueMultivare.get_total_time, time_on_dragger)
    toolbox.register("select", tools.selTournament, tournsize=15)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0 / len_orders)

    population = toolbox.populationCreator(n=POPULATION_SIZE)  # Создаем начальную популяцию
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("min", numpy.min)
    stats.register("avg", numpy.mean)

    population, logbook = eaSimpleWithElitism(population, toolbox,
                                              cxpb=P_CROSSOVER,
                                              mutpb=P_MUTATION,
                                              ngen=MAX_GENERATIONS,
                                              stats=stats,
                                              halloffame=hof,
                                              verbose=True)

    print("- Лучшие решения:")
    for i in range(HALL_OF_FAME_SIZE):
        print(i, ": ", hof.items[i].fitness.values[0], " -> ", hof.items[i])

    best_order = hof.items[0]  # массив заказов в виде индексов
    queue_multivare.queue = converting_indexes_to_numbers(best_order, orders)
    queue_multivare.setting_time_setup()
    #
    queue_multivare.calculating_basket()
    # queue_dragger(Dragger.queue_dragger.orders)
    # print("Лучший индивидуум =", queue_multivare.queue)
    print("Лучший индивидуум =", best_order)

    end = datetime.datetime.now()
    print(end - start)

    # minFitnessValues, meanFitnessValues = logbook.select("min", "avg")
    #
    # plt.plot(minFitnessValues, color='red')
    # plt.plot(meanFitnessValues, color='green')
    # plt.xlabel('Поколение')
    # plt.ylabel('Мин/средняя приспособленность')
    # plt.title('Зависимость максимальной и средней приспособленности от поколения')
    # plt.show()

    print("Время лучшего:", hof.items[0].fitness.values[0])

    # total_setup_time = check_list_multik.calculate_time_setup()
    #     # print('Время настройки2:', total_setup_time)


def main_dragger(orders: list):
    start = datetime.datetime.now()
    len_orders = len(orders)

    # # константы задачи
    HALL_OF_FAME_SIZE = len_orders * 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE = len_orders * 150  # количество индивидуумов в популяции
    MAX_GENERATIONS = int(len_orders * 0.9)  # максимальное количество поколений
    NUM_OF_VEHICLES = queue_dragger.num_basket
    print(NUM_OF_VEHICLES)
    indexes_baskets = [i for i in range(len_orders - NUM_OF_VEHICLES, len_orders)]
    time_on_multivare = queue_dragger.form_matrix_dragger(orders)
    toolbox = base.Toolbox()

    df = pd.DataFrame(time_on_multivare)

    mode = "w" if os.path.exists("excel/matrix_time.xlsx") else "a"

    with ExcelWriter("excel/matrix_time.xlsx", mode=mode, engine="openpyxl") as writer:
        df.to_excel(writer)

    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # стратегия приспособления - минимальное время
    creator.create("Individual", list, typecode='i', fitness=creator.FitnessMin)  # представление индивидуумов
    toolbox.register("randomOrder", random.sample, range(len_orders), len_orders)
    toolbox.register("individualCreator", tools.initIterate, creator.Individual, toolbox.randomOrder)
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)
    toolbox.register("evaluate", QueueDragger.get_cost, time_on_multivare, indexes_baskets)
    toolbox.register("select", tools.selTournament, tournsize=15)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0 / len_orders)

    population = toolbox.populationCreator(n=POPULATION_SIZE)  # Создаем начальную популяцию
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("min", numpy.min)
    stats.register("avg", numpy.mean)

    population, logbook = eaSimpleWithElitism(population, toolbox,
                                              cxpb=P_CROSSOVER,
                                              mutpb=P_MUTATION,
                                              ngen=MAX_GENERATIONS,
                                              stats=stats,
                                              halloffame=hof,
                                              verbose=True)

    print("- Лучшие решения:")
    for i in range(HALL_OF_FAME_SIZE):
        print(i, ": ", hof.items[i].fitness.values[0], " -> ", hof.items[i])

    best_order = hof.items[0]  # массив заказов в виде индексов
    # queue_dragger.queue = converting_indexes_to_numbers(best_order, orders)

    # for num, i in enumerate(best_order):
    #
    #     # пропускаем первый индекс, т.к у него нет время на перенастройку
    #     if num == 0:
    #         continue
    #
    #     orders[i].time_setup = queue_dragger.calculate_setup_time_dragger[i][best_order[num-1]]

    # queue_dragger(Dragger.queue_dragger.orders)
    print("Лучший индивидуум =", best_order)
    output = "Лучший индивидуум = "
    i = 0
    for order in best_order:
        if issubclass(consts.Order, type(orders[order].order)):
            output += '{}, '.format(orders[order].account_number)
        elif issubclass(Basket, type(orders[order].order)):
            output += 'Корзина {} время работы: {}ч. {}мин., '.format(i, str(orders[indexes_baskets[i]].order.time_work // 60),
                                                                      str(round(orders[indexes_baskets[i]].order.time_work % 60, 2)))
            i += 1

    print(output)
    end = datetime.datetime.now()
    print(end - start)

    minFitnessValues, meanFitnessValues = logbook.select("min", "avg")

    # plt.plot(minFitnessValues, color='red')
    # plt.plot(meanFitnessValues, color='green')
    # plt.xlabel('Поколение')
    # plt.ylabel('Мин/средняя приспособленность')
    # plt.title('Зависимость максимальной и средней приспособленности от поколения')
    # plt.show()

    print("Время лучшего:", hof.items[i].fitness.values[0])

    # total_setup_time = check_list_multik.calculate_time_setup()
    #     # print('Время настройки2:', total_setup_time)

# def queue_dragger(orders: [TaskForMultik]):
#     indexes_baskets = []
#     for order in orders:
#         if issubclass(Basket, type(order)):
#             indexes_baskets.append(orders.index(order))
#
