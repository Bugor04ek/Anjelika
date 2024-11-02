import datetime
import numpy as np
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import random
import matplotlib.pyplot as plt
import numpy

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


def varAnd(population, toolbox, cxpb, mutpb):
    offspring = [toolbox.clone(ind) for ind in population]

    # Apply crossover and mutation on the offspring
    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            toolbox.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values  # Удаление старого значения fitness
            del offspring[i].fitness.values  # Удаление старого значения fitness

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


def main_multivare(orders: list[MultivareTask]):
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

    def __init__(self, orders, ):

        HALL_OF_FAME_SIZE = len(orders) * 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
        POPULATION_SIZE = len(orders) * 200  # количество индивидуумов в популяции
        MAX_GENERATIONS = len(orders)  # максимальное количество поколений
        P_CROSSOVER = 1  # вероятность скрещивания
        P_MUTATION = 0  # вероятность мутации индивидуума

        self.limit_draggers = {
            'new':
                {
                    'diameter_min': 1.35,
                    'diameter_max': 4.54,
                    'Basket': True,
                    'Material': 'Cu',
                },
            'old':
                {
                    'diameter_min': 1.13,
                    'diameter_max': 2.95,
                    'Basket': False,
                    'Material': 'Cu',
                },
            'Al':
                {
                    'diameter_min': 1.68,
                    'diameter_max': 4.54,
                    'Basket': False,
                    'Material': 'Al',
                }
        }
        self.orders = orders
        self.time_setup_old = self.form_matrix_dragger('old')  # Матрица для 'old'
        self.time_setup_new = self.form_matrix_dragger('new')  # Матрица для 'new'
        self.time_setup_Al = self.form_matrix_dragger('Al')  # Матрица для 'Al'
        self.equipment = list(self.limit_draggers.keys())
        self.num_orders = len(orders)

        # Создаем классы для минимизации задачи
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", dict, fitness=creator.FitnessMin)

        # Базовые инструменты DEAP
        self.toolbox = base.Toolbox()
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self.generate_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("randomOrder", random.sample, range(self.num_orders), self.num_orders)
        self.toolbox.register("individualCreator", tools.initIterate, creator.Individual, self.toolbox.randomOrder)
        self.toolbox.register("populationCreator", tools.initRepeat, list, self.toolbox.individualCreator)

        population = self.toolbox.population(n=POPULATION_SIZE)

        self.toolbox.register("evaluate", self.get_cost)
        self.toolbox.register("select", tools.selTournament, tournsize=2)
        self.toolbox.register("mate", self.mate)
        self.toolbox.register("mutate", self.mutate)
        hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

        stats = tools.Statistics(lambda ind: ind.fitness.values)

        stats.register("avg", numpy.mean)
        stats.register("min", numpy.min)

        population, logbook = eaSimpleWithElitism(
            population, self.toolbox,
            cxpb=P_CROSSOVER,
            mutpb=P_MUTATION,
            ngen=MAX_GENERATIONS,
            stats=stats,
            halloffame=hof,
            verbose=True
        )

        print("- Лучшие решения:")
        # for i in range(HALL_OF_FAME_SIZE):
        #     print(i, ": ", hof.items[i].fitness.values[0], " -> ", hof.items[i])

        self.best_order = hof.items[0]  # массив заказов в виде индексов
        print(self.best_order)

        for equipment in self.equipment:
            globals()['queue_dragger_{}_dragger'.format(equipment)].queue = converting_indexes_to_numbers(self.best_order[equipment], orders)
            # queue_dragger_old_dragger.queue = converting_indexes_to_numbers(self.best_order['old'], orders)
            # queue_dragger_Al_dragger.queue = converting_indexes_to_numbers(self.best_order['Al'], orders)
            globals()['queue_dragger_{}_dragger'.format(equipment)].setting_time_setup()
            # queue_dragger_old_dragger.setting_time_setup()
            # queue_dragger_Al_dragger.setting_time_setup()

        for equipment in self.equipment:
            getattr(self, "print_{}".format(equipment))()

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
            temp_equipment = self.equipment.copy()
            while True:
                if len(temp_equipment):
                    equipment = random.choice(temp_equipment)
                else:
                    break
                if self.check_limit(equipment, order):
                    ind[equipment].append(order)
                    break
                else:
                    temp_equipment.remove(equipment)
                    continue

        return ind

    def check_limit(self, machine, i_order):
        order = TaskForDragger.orders[i_order].order
        is_basket: bool = isinstance(order, Basket)
        d = order.diameter

        if is_basket:
            material = 'Cu'
        else:
            m = order.mark.cable_parameters.get('Material', "")
            material = 'Al' if m == 'А' else 'Cu'

        current_machine = self.limit_draggers[machine]

        if (d < current_machine['diameter_min'] or d > current_machine['diameter_max'] or material != current_machine[
            'Material']
                or (is_basket and not current_machine['Basket'])):
            return False
        else:
            return True

    @staticmethod
    def calculate_setup_time_new_dragger(previous_order: TaskForDragger, order: TaskForDragger) -> float:
        """
        Создается матрица "расстояний"
        Считается время перенастройки оборудования для пары заказов и смены катушки
        Не учитывается добавление катушки, если она заполнена
        :param previous_order: предыдущий заказ
        :param order: текущий заказ
        :return: время настройки между двумя заказами
        """

        total_setup_time = 0

        if previous_order is not None:

            change = False

            """
                1 ПРОВЕРКА -- Разность диаметров
            """

            # больше фильер -> меньше диаметр
            if previous_order.spin > order.spin:
                removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
                total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
                total_setup_time += INSERT_SPIN * 1  # Время на установку фильер
                change = True
            # меньше фильер -> больше диаметр
            elif previous_order.spin < order.spin:
                removed_spin = 1  # Всегда снимаем фильеру с конца волочилки, т.к. если фильер меньше, тогда последняя ставится всегда в конец волочилки
                total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
                total_setup_time += INSERT_SPIN * (order.spin - (
                        previous_order.spin - 1))  # время на установку фильер -1, потому что 1 уже снята
                change = True
            elif previous_order.spin == order.spin and previous_order.diameter != order.diameter:
                total_setup_time += 1 * REMOVED_SPIN  # время на снятие 1 фильеры
                total_setup_time += 1 * INSERT_SPIN  # время на снятие 1 фильеры

            if change:
                # Если было любое изменение, то надо сменить катушку
                total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

        return total_setup_time

    @staticmethod
    def calculate_setup_time_old_dragger(previous_order: TaskForDragger, order: TaskForDragger) -> float:
        """
        Создается матрица "расстояний"
        Считается время перенастройки оборудования для пары заказов и смены катушки
        Не учитывается добавление катушки, если она заполнена
        :param previous_order: предыдущий заказ
        :param order: текущий заказ
        :return: время настройки между двумя заказами
        """

        total_setup_time = 0

        if previous_order is not None:

            change = False

            """
                1 ПРОВЕРКА -- Разность диаметров
            """

            # больше фильер -> меньше диаметр
            if previous_order.spin > order.spin:
                removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
                total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
                total_setup_time += INSERT_SPIN * 1  # Время на установку фильер
                change = True
            # меньше фильер -> больше диаметр
            elif previous_order.spin < order.spin:
                removed_spin = 1  # Всегда снимаем фильеру с конца волочилки, т.к. если фильер меньше, тогда последняя ставится всегда в конец волочилки
                total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
                total_setup_time += INSERT_SPIN * (order.spin - (
                        previous_order.spin - 1))  # время на установку фильер -1, потому что 1 уже снята
                change = True

            if change:
                # Если было любое изменение, то надо сменить катушку
                total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

        return total_setup_time

    def form_matrix_dragger(self, type_equipment: str):
        """
        Функция для создания матрицы времени перенастроек мультика
        :param type_equipment: тип волочилки new/old
        :return: матрица времени перенастроек
        """

        if type_equipment == 'old':
            method = 'calculate_setup_time_old_dragger'
        else:
            method = 'calculate_setup_time_new_dragger'

        temp_matrix1 = []
        for order1 in self.orders:
            temp_matrix2 = []
            for order2 in self.orders:
                temp_matrix2.append(getattr(self, method)(order1, order2))
            temp_matrix1.append(temp_matrix2)
        return temp_matrix1

    def get_cost(self, individual):
        """Функция фитнеса: вычисляем полное время выполнения, с учётом перенастроек и одинакового времени обработки"""
        total_time = {
            'new': 0,
            'old': 0,
            'Al': 0,
        }  # Время работы для каждого оборудования (new, old, Al)

        for equipment in self.equipment:
            orders = individual[equipment]
            if not orders:
                continue  # Если нет заказов на оборудовании, пропускаем

            # Выбираем соответствующую матрицу перенастроек
            time_on_dragger = getattr(self, "time_setup_{}".format(equipment))
            total_time[equipment] = getattr(self, "get_cost_{}".format(equipment))(time_on_dragger, orders)

        return sum(total_time.values()),  # Возвращаем суммарное время выполнения

    @staticmethod
    def get_cost_new(time_on_dragger, indices):

        indexes_baskets = QueueDragger.indexes_baskets
        total_time = 0  # суммарное время перенастроек
        num_downtime = 0  # количество простоев волочилки
        num_uptime = 0  # количесвто простоев мультика
        time_route_to_basket = 0

        # первая функция должная следить чтобы время работы + время перенастройки заказов были меньше чем разница между корзинами
        routes: [[int]] = QueueDragger.get_routes(indices)

        # контролируем число путей, чтобы не было подряд корзин
        if len(routes) <= len(indexes_baskets):
            total_time += 5000000
        else:

            reserve_time = TaskForDragger.orders[indexes_baskets[0]].order.time_work

            for route in range(len(indexes_baskets) - 1):

                time_route_to_basket += QueueDragger.get_time_route(routes[route], time_on_dragger, indexes_baskets,
                                                                    route)

                if reserve_time < time_route_to_basket < reserve_time + TaskForDragger.orders[
                    indexes_baskets[route + 1]].order.time_work:
                    reserve_time = TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work - (
                            time_route_to_basket - reserve_time)
                    if reserve_time < W:
                        num_downtime += 1
                elif time_route_to_basket < reserve_time:
                    num_downtime += 1
                    reserve_time = TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work
                elif time_route_to_basket > reserve_time + TaskForDragger.orders[
                    indexes_baskets[route + 1]].order.time_work - W:
                    num_uptime += 1
                    reserve_time = TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work

                # total_time += time_route_to_basket
                time_route_to_basket = 0

            else:

                time_route_to_basket += QueueDragger.get_time_route(routes[-2], time_on_dragger, indexes_baskets,
                                                                    routes.index(routes[-2]))

                reserve_time = TaskForDragger.orders[indexes_baskets[-1]].order.time_work

                if reserve_time < time_route_to_basket < reserve_time + Multivare.QueueMultivare.rest_orders.time_work:
                    pass
                elif time_route_to_basket < reserve_time:
                    num_downtime += 1
                elif time_route_to_basket > reserve_time:
                    num_uptime += 1

                # total_time += time_route_to_basket

            # last_route_time = QueueDragger.get_time_route(routes[-1], time_on_dragger, indexes_baskets, routes.index(routes[-1]))

        # время между каждой парой заказов
        for i in range(len(indices) - 1):
            total_time += time_on_dragger[indices[i]][indices[i + 1]]

        return total_time + (20000 * num_downtime) + (20000 * num_uptime)

    @staticmethod
    def get_cost_old(time_on_dragger, indices):
        """
        Считается время перенастроек между заказов для текущей очереди
        :param time_on_dragger: время перенастроек для каждого заказа с каждым
        :param indices: текущий индивид (очередь).
        :return: Всё время перенастроек для текущей очереди
        """

        time = 0

        # время между каждой парой заказов
        for i in range(len(indices) - 1):
            time += time_on_dragger[indices[i]][indices[i + 1]]

        return time

    @staticmethod
    def get_cost_Al(time_on_dragger, indices):
        """
        Считается время перенастроек между заказов для текущей очереди
        :param time_on_dragger: время перенастроек для каждого заказа с каждым
        :param indices: текущий индивид (очередь).
        :return: Всё время перенастроек для текущей очереди
        """

        time = 0

        # время между каждой парой заказов
        for i in range(len(indices) - 1):
            time += time_on_dragger[indices[i]][indices[i + 1]]

        return time

    def mate(self, ind1, ind2):
        """Оператор скрещивания: Partially Matched Crossover (PMX) с новыми индексами."""

        # if random.randint(0,1) == 0:
        # Применяем PMX внутри каждого оборудования ('new', 'old', 'Al')
        for equipment in ['new', 'old', 'Al']:
            # Получаем количество заказов на данном оборудовании
            num_orders_ind1 = len(ind1[equipment])
            num_orders_ind2 = len(ind2[equipment])

            # Создаём новые индексы для заказов (от 0 до n)
            new_indices_ind1 = list(range(num_orders_ind1))
            new_indices_ind2 = list(range(num_orders_ind2))

            # Применяем PMX к новым индексам
            tools.cxUniformPartialyMatched(new_indices_ind1, new_indices_ind2, indpb=2.0 / self.num_orders)

            # Используем новые индексы, чтобы скрестить заказы, соответствующие этим индексам
            # Создаём новый список заказов для каждого индивида на основе новых индексов
            new_orders_ind1 = [ind1[equipment][i] for i in new_indices_ind1]
            new_orders_ind2 = [ind2[equipment][i] for i in new_indices_ind2]

            # Обновляем заказы после кроссовера
            ind1[equipment] = new_orders_ind1
            ind2[equipment] = new_orders_ind2
        # else:
        #     # Обмен заказами между 'new' и 'old', если это возможно по ограничениям
        #     for i in range(min(len(ind1['new']), len(ind2['old']))):
        #         order_new = ind1['new'][i]  # Индекс заказа для 'new'
        #         order_old = ind2['old'][i]  # Индекс заказа для 'old'
        #
        #         # Проверка ограничения на выполнение заказа
        #         if self.check_limit('old', order_new) and self.check_limit('new', order_old):
        #             # Обмен индексами заказов между 'new' и 'old'
        #             ind1['new'][i], ind2['old'][i] = ind2['old'][i], ind1['new'][i]

        return ind1, ind2

    def mutate(self, individual):
        """Оператор мутации: случайное перемешивание заказов на оборудовании"""
        for equipment in self.equipment:
            if random.random() < 0.1:  # Вероятность мутации
                tools.mutShuffleIndexes(individual[equipment],
                                        indpb=1.0 / self.num_orders)  # Перемешиваем заказы на оборудовании

    def print_new(self):
        output = ''
        i = 0
        total_time = 0
        temp_time1, temp_time2 = 0, 0
        x = [0]
        x1 = [0]
        y = [0.25]
        y1 = [0.5]
        for order in self.best_order['new']:
            if issubclass(consts.Order, type(self.orders[order].order)):
                total_time += self.orders[order].time_work + self.orders[order].time_setup
                output += '{} -- {} + {} = {}ч. {}мин\n'.format(
                    self.orders[order].account_number,
                    self.orders[order].time_work,
                    self.orders[order].time_setup,
                    round((self.orders[order].time_work + self.orders[order].time_setup) // 60, 0),
                    round((self.orders[order].time_work + self.orders[order].time_setup) % 60, 0)
                )

            elif issubclass(Basket, type(self.orders[order].order)):
                x1.append((temp_time1 + int(total_time)))
                x1.append((temp_time1 + int(total_time) + Dragger.W))
                y1.append(0.5)
                y1.append(0.5)
                x.append((temp_time2 + int(self.orders[QueueDragger.indexes_baskets[i]].order.time_work)))
                y.append(0.25)
                temp_time1 += total_time
                temp_time2 += int(self.orders[QueueDragger.indexes_baskets[i]].order.time_work)
                output += '{}ч. {}мин. -- {}мин. \n'.format(round(total_time // 60, 0), round(total_time % 60, 0),
                                                            round(total_time, 0))
                output += 'Корзина {} время работы на мультике: {}ч. {}мин. -- {}мин.\n'.format(
                    i, self.orders[QueueDragger.indexes_baskets[i]].order.time_work // 60,
                    round(self.orders[QueueDragger.indexes_baskets[i]].order.time_work % 60, 2),
                    round(self.orders[QueueDragger.indexes_baskets[i]].order.time_work, 0)
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

        # minFitnessValues, meanFitnessValues = self.logbook.select("min", "avg")

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

    def print_old(self):
        output = ''
        total_time = 0
        for order in self.best_order['old']:
            total_time += self.orders[order].time_work + self.orders[order].time_setup
            output += '{} -- {} + {} = {}ч. {}мин\n'.format(
                    self.orders[order].account_number,
                    self.orders[order].time_work,
                    self.orders[order].time_setup,
                    round((self.orders[order].time_work + self.orders[order].time_setup) // 60, 0),
                    round((self.orders[order].time_work + self.orders[order].time_setup) % 60, 0)
                )

        print(output)

    def print_Al(self):
        output = ''
        total_time = 0
        for order in self.best_order['Al']:
            total_time += self.orders[order].time_work + self.orders[order].time_setup
            output += '{} -- {} + {} = {}ч. {}мин\n'.format(
                self.orders[order].account_number,
                self.orders[order].time_work,
                self.orders[order].time_setup,
                round((self.orders[order].time_work + self.orders[order].time_setup) // 60, 0),
                round((self.orders[order].time_work + self.orders[order].time_setup) % 60, 0)
            )

        print(output)


def main_dragger(orders: list):
    start = datetime.datetime.now()
    len_orders = len(orders)
    NUM_OF_VEHICLES = queue_dragger_new_dragger.num_basket
    QueueDragger.indexes_baskets = [i for i in range(len_orders - NUM_OF_VEHICLES, len_orders)]
    GenetikDragger(orders)
    end = datetime.datetime.now()
    print(end - start)
#     #
#     # # константы задачи
#     HALL_OF_FAME_SIZE = len_orders * 10  # количеству индивидуумов, которых мы хотим хранить в зале славы
#     POPULATION_SIZE = len_orders * 200  # количество индивидуумов в популяции
#     MAX_GENERATIONS = len_orders  # максимальное количество поколений
#     NUM_OF_VEHICLES = queue_dragger_new_dragger.num_basket
#
#     time_on_dragger = QueueDragger.form_matrix_dragger(orders)
#     toolbox = base.Toolbox()
#
#     df = pd.DataFrame(time_on_dragger)
#
#     mode = "w" if os.path.exists("excel/matrix_time.xlsx") else "a"
#
#     with ExcelWriter("excel/matrix_time.xlsx", mode=mode, engine="openpyxl") as writer:
#         df.to_excel(writer)
#
#     creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # стратегия приспособления - минимальное время
#     creator.create("Individual", list, typecode='i', fitness=creator.FitnessMin)  # представление индивидуумов
#     toolbox.register("randomOrder", random.sample, range(len_orders), len_orders)
#     toolbox.register("individualCreator", tools.initIterate, creator.Individual, toolbox.randomOrder)
#     toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)
#     toolbox.register("evaluate", QueueDragger.get_cost, time_on_dragger)
#     toolbox.register("select", tools.selTournament, tournsize=2)
#     toolbox.register("mate", tools.cxUniformPartialyMatched, indpb=2.0 / len_orders)
#     toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1.0 / len_orders)
#
#     population = toolbox.populationCreator(n=POPULATION_SIZE)  # Создаем начальную популяцию
#     hof = tools.HallOfFame(HALL_OF_FAME_SIZE)
#
#     stats = tools.Statistics(lambda ind: ind.fitness.values)
#
#     stats.register("min", numpy.min)
#     stats.register("avg", numpy.mean)
#
#     population, logbook = eaSimpleWithElitism(
#         population, toolbox,
#         cxpb=P_CROSSOVER,
#         mutpb=P_MUTATION,
#         ngen=MAX_GENERATIONS,
#         stats=stats,
#         halloffame=hof,
#         verbose=True
#     )
#
#     print("- Лучшие решения:")
#     for i in range(HALL_OF_FAME_SIZE):
#         print(i, ": ", hof.items[i].fitness.values[0], " -> ", hof.items[i])
#
#     best_order = hof.items[0]  # массив заказов в виде индексов
#     # queue_dragger.queue = converting_indexes_to_numbers(best_order, orders)
#     # queue_dragger.setting_time_setup()
#
#     print("Лучший индивидуум =", best_order)
#     output = "Лучший индивидуум = \n"
#     i = 0
#     total_time = 0
#     temp_time1, temp_time2 = 0, 0
#     x = [0]
#     x1 = [0]
#     y = [0.25]
#     y1 = [0.5]
#     for order in best_order:
#         if issubclass(consts.Order, type(orders[order].order)):
#             total_time += orders[order].time_work + orders[order].time_setup
#             output += '{} -- {} + {} = {}ч. {}мин\n'.format(
#                 orders[order].account_number,
#                 orders[order].time_work,
#                 orders[order].time_setup,
#                 round((orders[order].time_work + orders[order].time_setup) // 60, 0),
#                 round((orders[order].time_work + orders[order].time_setup) % 60, 0)
#             )
#
#         elif issubclass(Basket, type(orders[order].order)):
#             x1.append((temp_time1 + int(total_time)))
#             x1.append((temp_time1 + int(total_time) + Dragger.W))
#             y1.append(0.5)
#             y1.append(0.5)
#             x.append((temp_time2 + int(orders[QueueDragger.indexes_baskets[i]].order.time_work)))
#             y.append(0.25)
#             temp_time1 += total_time
#             temp_time2 += int(orders[QueueDragger.indexes_baskets[i]].order.time_work)
#             output += '{}ч. {}мин. -- {}мин. \n'.format(round(total_time // 60, 0), round(total_time % 60, 0),
#                                                         round(total_time, 0))
#             output += 'Корзина {} время работы на мультике: {}ч. {}мин. -- {}мин.\n'.format(
#                 i, orders[QueueDragger.indexes_baskets[i]].order.time_work // 60,
#                 round(orders[QueueDragger.indexes_baskets[i]].order.time_work % 60, 2),
#                 round(orders[QueueDragger.indexes_baskets[i]].order.time_work, 0)
#             )
#             output += 'Корзина {} время работы -- {}ч\n'.format(i, Dragger.W // 60)
#             i += 1
#             total_time = 0
#             total_time += Dragger.W
#     else:
#         x1.append((temp_time1 + int(total_time)))
#         y1.append(0.5)
#         output += '{}ч. {}мин. \n'.format(total_time // 60, total_time % 60)
#         output += 'остаток {} на мультике Корзина {} время работы: {}ч. {}мин., \n'.format(
#             Multivare.QueueMultivare.rest_basket,
#             i,
#             str(Multivare.QueueMultivare.rest_orders.time_work // 60),
#             str(round(Multivare.QueueMultivare.rest_orders.time_work % 60, 2))
#         )
#     print(output)
#     end = datetime.datetime.now()
#     print(end - start)
#
#     minFitnessValues, meanFitnessValues = logbook.select("min", "avg")
#
#     # Add annotations
#     for i, (xi, yi) in enumerate(zip(x, y)):
#         plt.annotate(f'{int(xi)}', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center')
#
#     plt.plot(x, y, marker='|', linestyle='-', color='red')
#
#     for i, (xi, yi) in enumerate(zip(x1, y1)):
#         plt.annotate(f'{int(xi)}', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center')
#
#     plt.plot(x1, y1, marker='|', linestyle='-', color='green')
#     plt.grid(True)
#     # plt.plot(x, y, color='red')
#     # plt.plot(x1, y1, color='green')
#     plt.locator_params(axis='x', nbins=5)
#     plt.locator_params(axis='y', nbins=1)
#     plt.ylim(0, 1)
#     plt.show()
#     # plt.plot(minFitnessValues, color='red')
#     # plt.plot(meanFitnessValues, color='green')
#     # plt.xlabel('Поколение')
#     # plt.ylabel('Мин/средняя приспособленность')
#     # plt.title('Зависимость максимальной и средней приспособленности от поколения')
#     # plt.show()
#
#     print("Время лучшего:", hof.items[i].fitness.values[0])
#
#     total_setup_time = check_list_multik.calculate_time_setup()
#     print('Время настройки2:', total_setup_time)
#
# # def queue_dragger(orders: [TaskForMultik]):
# #     indexes_baskets = []
# #     for order in orders:
# #         if issubclass(Basket, type(order)):
# #             indexes_baskets.append(orders.index(order))
# #
