import Оборудование.Multivare as Multivare

REMOVED_SPIN = 1  # время снятия фильер
INSERT_SPIN = 5  # время вставки фильер
CHANGE_BOBBIN = 5  # смена катушки
CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
STRETCHING_WIRE = 5  # протягивание проволочки в отжиге

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

    def __init__(self, order, diameter):
        self.order = order
        self.IDZak = order.IDZak
        self.account_number = order.account_number
        self.diameter = diameter
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
        return '{} IDZak {}'.format(self.account_number, self.IDZak)


class QueueDragger:
    """
    Класс очереди волочилки. В очереди могут быть либо заказы идущие на волочилку и не мультик,
    либо корзины, состоящие из заказов на мультик
    """

    def __init__(self):
        self.orders = []

    def __add__(self, other):
        self.orders.append(other)

    def __str__(self):
        res = ''

        for orders in self.orders:

            if issubclass(Multivare.Basket, type(orders)):
                res += 'Корзина (Время работы заказов = {}ч. {}мин.; Длина {}): {}'.format(str(orders.time_work // 60),
                                                                                           str(round(
                                                                                               orders.time_work % 60,
                                                                                               2)), orders.sum_basket,
                                                                                           orders.__str__())
            elif issubclass(TaskForDragger, type(orders)):
                res += 'Заказ на мультик {} \n'.format(orders.__repr__())

        return res + '\n'

    @staticmethod
    def calculate_setup_time_dragger(previous_order, order) -> float:
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
    def form_matrix_multivare(orders):
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
    def get_cost():

        # первая функция должная следить чтобы время работы + время перенастройки заказов были меньше чем разница между корзинами
        # вторая функция возвращает время перенастроек

        pass


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
