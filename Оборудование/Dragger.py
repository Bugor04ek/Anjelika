import consts
import Оборудование.Multivare as Multivare

REMOVED_SPIN = 1  # время снятия фильер
INSERT_SPIN = 5  # время вставки фильер
CHANGE_BOBBIN = 5  # смена катушки
CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
STRETCHING_WIRE = 5  # протягивание проволочки в отжиге
W = 12 * 60  # время изготовления 8 корзин

dictionary_spinners_new_dragger = {
    7: 1,
    5.75: 2,
    4.8: 3,
    4.03: 4,
    3.43: 5,
    2.95: 6,
    2.56: 7,
    2.25: 8,
    1.99: 9,
    1.78: 10,
    1.58: 11,
    1.41: 12,
    1.35: 13,
    1.25: 14,
}
dictionary_spinners_old_dragger = {
    7: 1,
    6.80: 2,
    5.15: 3,
    4.50: 4,
    3.90: 5,
    3.45: 6,
    2.95: 7,
    2.60: 8,
    2.00: 9,
    1.65: 10,
    1.40: 11,
    1.15: 12,
}
dictionary_spinners_al_dragger = {
    9: 1,
    8.15: 2,
    7.05: 3,
    6.15: 4,
    5.39: 5,
    4.72: 6,
    4.14: 7,
    3.64: 8,
    3.20: 9,
    2.80: 10,
    2.48: 11,
    2.20: 12,
    1.93: 13,
    1.70: 14,
}


class TaskForDragger:
    """
    Класс для заказов на волочение. Тут может быть либо обычный заказ, либо корзина состоящая из заказов на мультик.
    """

    # Переменная класса для подсчета индексов
    orders = []

    def __init__(self, order):
        TaskForDragger.orders.append(self)
        # if order.mark.mark[0] == 'А':
        #     self.type_of_equipment = 'queue_dragger_al_dragger'
        #     a = globals()[self.type_of_equipment]
        # else:
        #     self.type_of_equipment = None

        self.id = len(TaskForDragger.orders)
        self.order = order
        if issubclass(consts.Order, type(order)):
            self.IDZak = order.IDZak
            self.account_number = order.account_number
            self.time_work = order.time_on_dragger
            self.diameter = order.diameter
        elif issubclass(Multivare.Basket, type(order)):
            self.time_work = W
            self.diameter = Multivare.d_mult

        self.time_setup = 0
        self.spin = self.counting_spinners()

    def counting_spinners(self):
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        Если находим в справочнике значение фильеры, тогда количество = ключ
        Если не находим, тогда ищем после какой фильеры нужно поставить еще одну количество = ключ + 1
        """

        # Определяет стандартные фильеры или нужна дополнительная
        extra_spin = dictionary_spinners_new_dragger.get(self.diameter, 0)

        # Если extra_spin == 0, значит есть доп фильера
        # Иначе количество фильер = self.extra_spin

        return extra_spin if extra_spin else self.counting_extra_spin()

    def counting_extra_spin(self) -> int:
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        Если находим в справочнике значение фильеры, тогда количество = ключ
        Если не находим, тогда ищем после какой фильеры нужно поставить еще одну количество = ключ + 1
        :return: количество фильер
        """
        for k, v in sorted(dictionary_spinners_new_dragger.items()):
            if self.diameter < k:
                #  Рассчитывает количество фильер для заказа вместе с последней нестандартной фильерой
                return v + 1

    def __repr__(self):
        if issubclass(consts.Order, type(self.order)):
            return '{} {} IDZak {}'.format(self.id, self.account_number, self.IDZak)
        elif issubclass(Multivare.Basket, type(self.order)):
            return '{}'.format(self.order.__repr__())


class QueueDragger:
    """
    Класс очереди волочилки. В очереди могут быть либо заказы идущие на волочилку и не мультик,
    либо корзины, состоящие из заказов на мультик
    """
    indexes_baskets: [int] = []

    def __init__(self):
        self.__queue = []
        self.num_basket = 0

    @property
    def queue(self):
        return self.__queue

    @queue.setter
    def queue(self, orders):
        self.__queue = orders

    def append(self, other):
        self.__queue.append(other)
        self.num_basket += 1

    def __str__(self):
        res = ''

        for order in self.__queue:
            # elif issubclass(TaskForDragger, type(orders)):
            res += 'Заказ на мультик {} \n'.format(order.__repr__())

        return res + '\n'

    @staticmethod
    def get_cost(time_on_dragger, indices):

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

                time_route_to_basket += QueueDragger.get_time_route(routes[route], time_on_dragger, indexes_baskets, route)

                if reserve_time < time_route_to_basket < reserve_time + TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work:
                    reserve_time = TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work - (time_route_to_basket - reserve_time)
                    if reserve_time < W:
                        num_downtime += 1
                elif time_route_to_basket < reserve_time:
                    num_downtime += 1
                    reserve_time = TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work
                elif time_route_to_basket > reserve_time + TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work - W:
                    num_uptime += 1
                    reserve_time = TaskForDragger.orders[indexes_baskets[route + 1]].order.time_work

                # total_time += time_route_to_basket
                time_route_to_basket = 0

            else:

                time_route_to_basket += QueueDragger.get_time_route(routes[-2], time_on_dragger, indexes_baskets, routes.index(routes[-2]))

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

        return total_time + (20000 * num_downtime) + (20000 * num_uptime),

    @staticmethod
    def get_time_route(route: [int], time_on_multivare: [[]], indexes_baskets: [int], number_route: int):
        """
        Считается время работы + перенастройки между корзинами. route имеет вид [[],[],[]], поэтому, если number_route == 0,
        то перенастройки с корзины не будет, т.к. это первый путь. Запятые символизируют корзины
        :param route: массив индексов заказов одного из пути номером number_route
        :param time_on_multivare: матрица времени перенастроек
        :param indexes_baskets: массив индексов корзин
        :param number_route: номер пути
        :return: суммарное время работы
        """
        time = 0

        # перенастройка с предыдущей корзины
        time += time_on_multivare[indexes_baskets[number_route - 1]][route[0]] if number_route else 0

        for i in range(len(route) - 1):
            time += TaskForDragger.orders[route[i]].time_work + time_on_multivare[route[i]][route[i + 1]]
        else:
            time += TaskForDragger.orders[route[-1]].time_work + time_on_multivare[route[-1]][indexes_baskets[0]]
        # добавляем время на изготовление 8 корзин
        time += (W if number_route else 0)

        return time

    @staticmethod
    def get_routes(indices):
        """
        Разбиваем индивида (очередь) на маршруты от корзины до корзины
        :param indices: текущая очередь
        :return: [[]]
        """
        routes = []
        route = []

        # loop over all indices in the list:
        for i in indices:

            # index is part of the current route:
            if i not in QueueDragger.indexes_baskets:
                route.append(i)

            # separator index - route is complete:
            elif len(route) > 0:
                routes.append(route)
                route = []  # reset route

        # append the last route:
        if route:
            routes.append(route)

        return routes

    @staticmethod
    def calculate_setup_time_dragger(previous_order: TaskForDragger, order: TaskForDragger) -> float:
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

    @staticmethod
    def form_matrix_dragger(orders):
        """
        Функция для создания матрицы времени перенастроек мультика
        :param orders: неупорядоченный список заказов на мультик
        :return: матрица времени перенастроек
        """
        temp_matrix1 = []
        for order1 in orders:
            temp_matrix2 = []
            for order2 in orders:
                temp_matrix2.append(QueueDragger.calculate_setup_time_dragger(order1, order2))
            temp_matrix1.append(temp_matrix2)
        return temp_matrix1

    def setting_time_setup(self):
        """
        Определяем время настройки заказов на мультике.
        :return:
        """

        for i in range(len(self.__queue)):

            # пропускаем первый индекс, т.к у него нет время на перенастройку
            if i == 0:
                continue

            self.__queue[i].time_setup = QueueDragger.calculate_setup_time_dragger(self.__queue[i - 1],
                                                                                   self.__queue[i])


class Bobbin:
    count = 0

    def __init__(self, volume, max_volume, date, order):
        Bobbin.count += 1
        self.number = Bobbin.count
        self.max_volume = max_volume
        self.date_first_order = date
        self.volume: float = 0
        # self.orders: [TaskForMultik] = []
        self.time_on_mult: float = 0
        self.add(volume, order)

    def add(self, volume, order):
        if volume != 0 and order is not None:
            self.volume += volume
            self.orders.append(order)
            self.time_on_mult += order.time_on_mult


queue_dragger_new_dragger = QueueDragger()
queue_dragger_old_dragger = QueueDragger()
queue_dragger_al_dragger = QueueDragger()
