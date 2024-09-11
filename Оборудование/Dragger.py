import consts
import Оборудование.Multivare as Multivare

REMOVED_SPIN = 1  # время снятия фильер
INSERT_SPIN = 5  # время вставки фильер
CHANGE_BOBBIN = 5  # смена катушки
CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
STRETCHING_WIRE = 5  # протягивание проволочки в отжиге
W = 12 * 60  # время изготовления 8 корзин

dictionary_spinners = {
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


class TaskForDragger:
    """
    Класс для заказов на волочение.
    """

    orders = []

    def __init__(self, order):
        TaskForDragger.orders.append(self)
        self.id = len(TaskForDragger.orders)
        self.order = order
        if issubclass(consts.Order, type(order)):
            self.IDZak = order.IDZak
            self.account_number = order.account_number
            self.time_work = order.time_on_dragger
            self.diameter = order.diameter
        elif issubclass(Multivare.Basket, type(order)):
            self.time_work = order.time_work
            self.diameter = Multivare.d_mult

        self.time_setup = 0
        self.extra_spin = self.extra_spin()
        self.spin = self.counting_spinners()

    def counting_spinners(self):
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        Если находим в справочнике значение фильеры, тогда количество = ключ
        Если не находим, тогда ищем после какой фильеры нужно поставить еще одну количество = ключ + 1
        """

        # Если spin == 0, значит есть доп фильера
        # Иначе количество фильер = spin
        return self.extra_spin if self.extra_spin else self.counting_extra_spin()

    def extra_spin(self):
        """
        Определяет стандартные фильеры или нужна дополнительная
        :return: 0, если нет диметра в справочнике -- значит будет доп фильера. Int - количество фильер
        """
        return dictionary_spinners.get(self.diameter, 0)

    def counting_extra_spin(self) -> int:
        """
        Рассчитывает количество фильер для заказа вместе с последней нестандартной фильерой
        :return: количество фильер
        """
        for k, v in sorted(dictionary_spinners.items()):
            if self.diameter < k:
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

    @staticmethod
    def get_cost(time_on_multivare, indices):

        indexes_baskets = QueueDragger.indexes_baskets
        total_time = 0
        max_route_time = 0
        time_route_to_basket = 0

        # первая функция должная следить чтобы время работы + время перенастройки заказов были меньше чем разница между корзинами
        routes: [[int]] = QueueDragger.get_routes(indices)

        # контролируем число путей, чтобы не было подряд корзин
        if len(routes) != len(indexes_baskets):
            total_time += 3000
        else:

            for route in range(len(indexes_baskets) - 1):
                # складываем время до корзины
                for r1 in routes[route]:
                    time_route_to_basket += time_on_multivare[indices[r1]][indices[r1 + 1]] + TaskForDragger.orders[r1].time_work
                # складываем время после корзины
                for r2 in routes[route + 1]:
                    time_route_to_basket += time_on_multivare[indices[r2]][indices[r2 + 1]] + TaskForDragger.orders[r2].time_work
                # проверяем сколько времени есть в запасе для заказов на волочение

                reserve_time = TaskForDragger.orders[indexes_baskets[route]].time_work + TaskForDragger.orders[indexes_baskets[route + 1]].time_work - W
                # если время работы заказов превышает запасы для корзин
                if time_route_to_basket > reserve_time:
                    total_time += 1000 #time_route_to_basket - reserve_time
                    time_route_to_basket = 0
            else:
                # складываем время до корзины
                for r1 in routes[route]:
                    time_route_to_basket += time_on_multivare[indices[r1]][indices[r1 + 1]] + TaskForDragger.orders[
                        r1].time_work
                # складываем время после корзины
                for r2 in routes[route + 1]:
                    time_route_to_basket += time_on_multivare[indices[r2]][indices[r2 + 1]] + TaskForDragger.orders[
                        r2].time_work
                # проверяем сколько времени есть в запасе для заказов на волочение

                reserve_time = TaskForDragger.orders[indexes_baskets[route+1]].time_work + Multivare.QueueMultivare.rest_orders.time_work - W
                # если время работы заказов превышает запасы для корзин
                if time_route_to_basket > reserve_time:
                    total_time += 1000 # time_route_to_basket - reserve_time
                    time_route_to_basket = 0



        # вторая функция возвращает время перенастроек

        # уменьшаем длину максимального маршрута
        for route in routes:
            route_time = QueueDragger.get_time_route(route, time_on_multivare)
            max_route_time = max(route_time, max_route_time)

        # for i in range(len(indices) - 1):
        #     total_time += time_on_multivare[indices[i]][indices[i + 1]]

        return max_route_time + total_time,

    @staticmethod
    def get_time_route(route, time_on_multivare):
        time = 0
        for i in range(len(route) - 1):
            time += time_on_multivare[i][i + 1]
        return time

    @staticmethod
    def get_routes(indices):
        # initialize lists:
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


queue_dragger = QueueDragger()
