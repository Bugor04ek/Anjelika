from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import random
import matplotlib.pyplot as plt
import numpy
import os
from pandas import ExcelWriter
import pandas as pd
from consts import converting_indexes_to_numbers
from Оборудование.Multivare import *

# константы задачи
HALL_OF_FAME_SIZE = 30  # количеству индивидуумов, которых мы хотим хранить в зале славы

# константы генетического алгоритма
POPULATION_SIZE = 10200  # количество индивидуумов в популяции
P_CROSSOVER = 1  # вероятность скрещивания
P_MUTATION = 0  # вероятность мутации индивидуума
MAX_GENERATIONS = 30  # максимальное количество поколений


# Функция для расчета времени перенастройки между заказами мультика
def calculate_setup_time_multivare(previous_order, order):
    # Создается матрица "расстояний".
    # Считается время перенастройки и смены катушки между заказами
    # Не учитывается добавление катушки, если она заполнена
    # После определения оптимального варианта будет пересчет через чеклист мультика

    total_setup_time = 0

    if previous_order is not None:

        change = False

        """
            1 ПРОВЕРКА -- Разность диаметров
        """

        # меньше диаметр - больше фильер
        if previous_order.spin > order.spin:
            removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
            total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
            total_setup_time += INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер
            change = True
        # больше диаметр - меньше фильер
        elif previous_order.spin < order.spin:
            removed_spin = 1  # снимаем последнюю
            total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
            total_setup_time += INSERT_SPIN * (
                    order.spin - (
                    previous_order.spin - 1)) * order.wires_in_sliver  # время на установку фильер +1, потому 1 уже снята tt
            change = True

        """
            2 ПРОВЕРКА -- Разность проволочек
        """

        dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

        if previous_order.wires_in_sliver < order.wires_in_sliver:
            # Надо протянуть новые проволочки через все фильеры на новом заказе
            total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
            change = True
        elif previous_order.wires_in_sliver > order.wires_in_sliver:
            # Надо снять проволочки со всех фильер previous_order
            total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE
            change = True

        if change:
            # Если было любое изменение, то надо сменить катушку
            total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

    return total_setup_time
def calculate_setup_time_dragger(previous_order, order):
    # Создается матрица "расстояний".
    # Считается время перенастройки и смены катушки между заказами
    # Не учитывается добавление катушки, если она заполнена
    # После определения оптимального варианта будет пересчет через чеклист мультика

    total_setup_time = 0

    if previous_order is not None:

        change = False

        """
            1 ПРОВЕРКА -- Разность диаметров
        """

        # меньше диаметр - больше фильер
        if previous_order.spin > order.spin:
            removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
            total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
            total_setup_time += INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер
            change = True
        # больше диаметр - меньше фильер
        elif previous_order.spin < order.spin:
            removed_spin = 1  # снимаем последнюю
            total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
            total_setup_time += INSERT_SPIN * (
                    order.spin - (
                    previous_order.spin - 1)) * order.wires_in_sliver  # время на установку фильер +1, потому 1 уже снята tt
            change = True

        """
            2 ПРОВЕРКА -- Разность проволочек
        """

        dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

        if previous_order.wires_in_sliver < order.wires_in_sliver:
            # Надо протянуть новые проволочки через все фильеры на новом заказе
            total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
            change = True
        elif previous_order.wires_in_sliver > order.wires_in_sliver:
            # Надо снять проволочки со всех фильер previous_order
            total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE
            change = True

        if change:
            # Если было любое изменение, то надо сменить катушку
            total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

    return total_setup_time


# Функция для создания матрицы времени перенастроек мультика
def form_matrix_multivare(orders):
    temp_matrix1 = []
    for order1 in orders:
        temp_matrix2 = []
        for order2 in orders:
            temp_matrix2.append(calculate_setup_time_multivare(order1, order2))
        temp_matrix1.append(temp_matrix2)
    return temp_matrix1


def getTotalDistance(time_on_multivare, indices):
    """Calculates the total distance of the path described by the given indices of the cities

    :param indices: A list of ordered city indices describing the given path.
    :return: total distance of the path described by the given indices
    """
    # distance between th elast and first city:
    time = 0

    # add the distance between each pair of consequtive cities:
    for i in range(len(indices) - 1):
        time += time_on_multivare[indices[i]][indices[i + 1]]

    return time,


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


def main(orders: list[TaskForMultik]):
    len_orders = len(orders)
    time_on_multivare = form_matrix_multivare(orders)
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
    toolbox.register("evaluate", getTotalDistance, time_on_multivare)
    toolbox.register("select", tools.selTournament, tournsize=20)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.5 / len_orders)

    population = toolbox.populationCreator(n=POPULATION_SIZE)  # Создаем начальную популяцию
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("max", numpy.max)
    stats.register("avg", numpy.mean)

    population, logbook = eaSimpleWithElitism(population, toolbox,
                                              cxpb=P_CROSSOVER,
                                              mutpb=P_MUTATION,
                                              ngen=MAX_GENERATIONS,
                                              stats=stats,
                                              halloffame=hof,
                                              verbose=True)

    print("Индивидуумы в зале славы = ", *hof.items, sep="\n")
    print("Лучший индивидуум =", hof.items[0])

    queue_multivare.queue = converting_indexes_to_numbers(hof.items[0], orders)
    queue_multivare.all_orders()

    print("Лучший индивидуум =", queue_multivare.queue)

    maxFitnessValues, meanFitnessValues = logbook.select("max", "avg")

    plt.plot(maxFitnessValues, color='red')
    plt.plot(meanFitnessValues, color='green')
    plt.xlabel('Поколение')
    plt.ylabel('Макс/средняя приспособленность')
    plt.title('Зависимость максимальной и средней приспособленности от поколения')
    plt.show()

    print("Время лучшего:", getTotalDistance(time_on_multivare, hof.items[0]))

    # total_setup_time = check_list_multik.calculate_time_setup()
    # print('Время настройки2:', total_setup_time)

