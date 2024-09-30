import datetime

import numpy as np
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
    POPULATION_SIZE = len_orders * 300  # количество индивидуумов в популяции
    MAX_GENERATIONS = int(len_orders * 0.9)  # максимальное количество поколений

    time_on_multivare = QueueMultivare.form_matrix_multivare(orders)
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
    toolbox.register("evaluate", QueueMultivare.get_total_time, time_on_multivare)
    toolbox.register("select", tools.selTournament, tournsize=15)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0 / len_orders)

    population = toolbox.populationCreator(n=POPULATION_SIZE)  # Создаем начальную популяцию
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("min", numpy.min)
    stats.register("avg", numpy.mean)

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


# Операции над генами: распределение заказов по оборудованию и порядку


class GenetikDragger:

    def __init__(self, num_orders, ):
        self.limit_draggers = {
            'new':
                {
                    'diameter_min': 1.37,
                    'diameter_max': 4.54,
                    'basket': True,
                    'Material': 'Cu',
                },
            'old':
                {
                    'diameter_min': 1.37,
                    'diameter_max': 1.37,
                    'basket': False,
                    'Material': 'Cu',
                },
            'Al':
                {
                    'diameter_min': 1.70,
                    'diameter_max': 4.54,
                    'basket': False,
                    'Material': 'Al',
                }
        }
        self.equipment = list(self.limit_draggers.keys())
        self.num_orders = num_orders

        # Создаем классы для минимизации задачи
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        # Базовые инструменты DEAP
        self.toolbox = base.Toolbox()
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self.generate_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("randomOrder", random.sample, range(num_orders), num_orders)
        self.toolbox.register("individualCreator", tools.initIterate, creator.Individual, self.toolbox.randomOrder)
        self.toolbox.register("populationCreator", tools.initRepeat, list, self.toolbox.individualCreator)

        population = self.toolbox.population(n=POPULATION_SIZE)

        self.toolbox.register("evaluate", QueueDragger.get_cost, time_on_dragger)
        self.toolbox.register("select", tools.selTournament, tournsize=2)
        self.toolbox.register("mate", tools.cxUniformPartialyMatched, indpb=2.0 / num_orders)
        self.toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0 / num_orders)

    def generate_individual(self):
        available_orders = list(range(self.num_orders))
        random.shuffle(available_orders)

        # Случайно разбиваем заказы между тремя оборудованиями
        ind = {
            'new': [],
            'old': [],
            'Al': [],
        }
        # [Заказы для оборудования 0, заказы для оборудования 1]
        for order in available_orders:
            temp_equipment = self.equipment
            while True:
                equipment = random.choice(temp_equipment)
                if self.check_limit(equipment, order):
                    ind[equipment].append(order)
                    break
                else:
                    temp_equipment.remove(equipment)
                    continue

        return ind

    def check_limit(self, machine, i_order):
        order = TaskForDragger.orders[i_order].order
        basket: bool = True if type(TaskForDragger.orders[i_order].order).__name__ == 'Basket' else False
        d = order.diameter

        if basket == 'Basket':
            material = 'Cu'
        else:
            m = order.mark.cable_parameters.get('Material', "")
            if m == '':
                material = 'Cu'
            else:
                material = 'Al' if m == 'А' else 'Cu'

        current_machine = self.limit_draggers[machine]

        if (d < current_machine['diameter_min']
                or d > current_machine['diameter_max']
                or basket != current_machine['Basket']
                or material != current_machine['Material']):
            return False
        else:
            return True


def main_dragger(orders: list):
    start = datetime.datetime.now()
    len_orders = len(orders)
    GenetikDragger(len_orders)

    # # константы задачи
    HALL_OF_FAME_SIZE = len_orders * 10   # количеству индивидуумов, которых мы хотим хранить в зале славы
    POPULATION_SIZE   = len_orders * 200  # количество индивидуумов в популяции
    MAX_GENERATIONS   = len_orders        # максимальное количество поколений
    NUM_OF_VEHICLES   = queue_dragger_new_dragger.num_basket

    QueueDragger.indexes_baskets = [i for i in range(len_orders - NUM_OF_VEHICLES, len_orders)]
    time_on_dragger = QueueDragger.form_matrix_dragger(orders)
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
    toolbox.register("evaluate", QueueDragger.get_cost, time_on_dragger)
    toolbox.register("select", tools.selTournament, tournsize=2)
    toolbox.register("mate", tools.cxUniformPartialyMatched, indpb=2.0 / len_orders)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0 / len_orders)

    population = toolbox.populationCreator(n=POPULATION_SIZE)  # Создаем начальную популяцию
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("min", numpy.min)
    stats.register("avg", numpy.mean)

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
    for i in range(HALL_OF_FAME_SIZE):
        print(i, ": ", hof.items[i].fitness.values[0], " -> ", hof.items[i])

    best_order = hof.items[0]  # массив заказов в виде индексов
    queue_dragger.queue = converting_indexes_to_numbers(best_order, orders)
    queue_dragger.setting_time_setup()

    print("Лучший индивидуум =", best_order)
    output = "Лучший индивидуум = \n"
    i = 0
    total_time = 0
    temp_time1, temp_time2 = 0, 0
    x = [0]
    x1 = [0]
    y = [0.25]
    y1 = [0.5]
    for order in best_order:
        if issubclass(consts.Order, type(orders[order].order)):
            total_time += orders[order].time_work + orders[order].time_setup
            output += '{} -- {} + {} = {}ч. {}мин\n'.format(
                orders[order].account_number,
                orders[order].time_work,
                orders[order].time_setup,
                round((orders[order].time_work + orders[order].time_setup) // 60, 0),
                round((orders[order].time_work + orders[order].time_setup) % 60, 0)
            )

        elif issubclass(Basket, type(orders[order].order)):
            x1.append((temp_time1 + int(total_time)))
            x1.append((temp_time1 + int(total_time) + Dragger.W))
            y1.append(0.5)
            y1.append(0.5)
            x.append((temp_time2 + int(orders[QueueDragger.indexes_baskets[i]].order.time_work)))
            y.append(0.25)
            temp_time1 += total_time
            temp_time2 += int(orders[QueueDragger.indexes_baskets[i]].order.time_work)
            output += '{}ч. {}мин. -- {}мин. \n'.format(round(total_time // 60, 0), round(total_time % 60, 0),
                                                        round(total_time, 0))
            output += 'Корзина {} время работы на мультике: {}ч. {}мин. -- {}мин.\n'.format(
                i, orders[QueueDragger.indexes_baskets[i]].order.time_work // 60,
                round(orders[QueueDragger.indexes_baskets[i]].order.time_work % 60, 2),
                round(orders[QueueDragger.indexes_baskets[i]].order.time_work, 0)
            )
            output += 'Корзина {} время работы -- {}ч\n'.format(i, Dragger.W // 60)
            i += 1
            total_time = 0
            total_time += Dragger.W
    else:
        x1.append((temp_time1 + int(total_time)))
        y1.append(0.5)
        output += '{}ч. {}мин. \n'.format(total_time // 60, total_time % 60)
        output += 'остаток {} на мультике Корзина {} время работы: {}ч. {}мин., \n'.format(
            Multivare.QueueMultivare.rest_basket,
            i,
            str(Multivare.QueueMultivare.rest_orders.time_work // 60),
            str(round(Multivare.QueueMultivare.rest_orders.time_work % 60, 2))
        )
    print(output)
    end = datetime.datetime.now()
    print(end - start)

    minFitnessValues, meanFitnessValues = logbook.select("min", "avg")

    # Add annotations
    for i, (xi, yi) in enumerate(zip(x, y)):
        plt.annotate(f'{int(xi)}', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center')

    plt.plot(x, y, marker='|', linestyle='-', color='red')

    for i, (xi, yi) in enumerate(zip(x1, y1)):
        plt.annotate(f'{int(xi)}', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center')

    plt.plot(x1, y1, marker='|', linestyle='-', color='green')
    plt.grid(True)
    # plt.plot(x, y, color='red')
    # plt.plot(x1, y1, color='green')
    plt.locator_params(axis='x', nbins=5)
    plt.locator_params(axis='y', nbins=1)
    plt.ylim(0, 1)
    plt.show()
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
