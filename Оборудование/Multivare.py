import os
import pandas as pd
from pandas import ExcelWriter
import consts
import Оборудование.Dragger as Dragger
from Оборудование.Equipments import MachineMeta

pi = 3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679821480865132823066470938446095

dict_key_group = {}


class MultivareMachine(metaclass=MachineMeta):
    REMOVED_SPIN = 1  # время снятия фильер
    INSERT_SPIN = 5  # время вставки фильер (это время надо умножить на количество проволочек в пряди)
    CHANGE_BASKET = 20  # смена корзины на мультике
    CHANGE_BOBBIN = 5  # смена катушки на мультике
    CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
    STRETCHING_WIRE = 5  # протягивание пучка проволочек после всех фильер
    KM_IN_1_BASKET = 35  # КМ в 1 корзине
    KM_IN_8_BASKET = KM_IN_1_BASKET * 8  # КМ в 8 корзинах

    dictionary_spinners = {
        2.28: 1,
        2.0264: 2,
        1.8: 3,
        1.6: 4,
        1.422: 5,
        1.2638: 6,
        1.1232: 7,
        0.9983: 8,
        0.8872: 9,
        0.7875: 10,
        0.6993: 11,
        0.621: 12,
        0.5514: 13,
        0.4896: 14,
        0.446: 15,
        0.4063: 16,
        0.3701: 17,
        0.3371: 18,
        0.3075: 19,
        0.2795: 20,
        0.26: 21
    }

    d_mult = 2.08
    pi = 3.141592653589793

    def __init__(self, name, capacity, supported_materials):
        self.name = name
        self.capacity = capacity
        self.supported_materials = supported_materials

    def is_suitable(self, material, quantity):
        return material in self.supported_materials and quantity <= self.capacity

    @classmethod
    def get_all_instances(cls, names=None):
        if names is None:
            return list(cls._instances)
        return [instance for instance in cls._instances if instance.name in names]


class MultivareTask(consts.Task):
    """
    Задание на мультик хранит в переменной класса хранит все заказы в массиве, их можно будет найти по IDZak
    """

    def __init__(self, order, diameter, number_of_veins, number_of_strands, number_of_sliver, wires_in_sliver, type):
        super().__init__(order, equipment_type='Multivare')
        # self.volume_bobbin = order.volume_bobbin
        # 350 - Ограничение по массе барабана для гибкой жилы на 630 барабан
        # 8.89 - Плотность меди
        self.volume_bobbin = 350 / (
                pi * 0.25 * 8.89 * order.diameter ** 2 * max(order.wires_in_sliver, order.wires_in_sliver_extra))
        self.IDZak = order.IDZak
        self.account_number = order.account_number + type
        self.diameter = diameter
        self.number_of_sliver = number_of_sliver
        self.wires_in_sliver = wires_in_sliver
        self.number_of_veins = number_of_veins
        self.number_of_strands = number_of_strands
        self.group = ()
        self.num_group = 0
        self.spin = 0
        self.total_weight_delays = 0
        self.length_piece = 0
        self.length_strands = 0
        self.full_bobbin = ()
        self.time_on_multivare = order.time_on_multivare
        self.time_on_mult_1_basket = 0
        self.__time_setup = 0
        self.num_basket = 0
        self.counting_spinners()
        self.set_group()
        self.calculating_length()

    def set_group(self) -> None:
        """
        Устанавливаем группу и номер группы для заказа
        """
        key = (self.spin, self.number_of_sliver, self.wires_in_sliver, self.order.type_bobbin)

        # группы без количества жил хз как там катушки меняются
        # key = (self.spin, self.wires_in_sliver, self.order.type_bobbin)

        if dict_key_group.get(key) is None:
            dict_key_group[key] = len(dict_key_group)

        self.group = key
        self.num_group = dict_key_group[key]

    def counting_spinners(self) -> None:
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        """

        self.spin = MultivareMachine.dictionary_spinners[
            min(MultivareMachine.dictionary_spinners, key=lambda x: abs(self.diameter - x))]

    def calculating_length(self):
        # суммарная длина проволочек

        self.total_weight_delays = ((self.number_of_sliver * self.wires_in_sliver) * self.number_of_strands *
                                    self.number_of_veins * self.order.order_length) * pi * 8.89 * (
                                           self.diameter ** 2) * 0.25
        self.length_piece = round(self.total_weight_delays * (self.diameter ** 2 / MultivareMachine.d_mult ** 2), 3)

        # 0 - сколько корзин по 8 штук нужно, если заказ очень большой и требуется много корзин
        # 1 - сколько корзин еще заполнится (набирается число до 8)
        self.num_basket = (int(self.total_weight_delays * 1 / (
                    pi * 0.25 * 8.89 * MultivareMachine.d_mult ** 2) / MultivareMachine.KM_IN_1_BASKET // 8),
                           self.total_weight_delays * 1 / (
                                       pi * 0.25 * 8.89 * MultivareMachine.d_mult ** 2) / MultivareMachine.KM_IN_1_BASKET % 8)
        self.time_on_mult_1_basket = self.time_on_multivare / (self.num_basket[0] + self.num_basket[1])

        # длина заказа в расчете на одну прядь (весь заказ это length_strands *
        # (number_of_sliver + number_of_sliver_extra))
        self.length_strands = round((self.order.order_length * self.number_of_veins * self.number_of_strands), 2)

        # подсчет барабанов
        self.calculating_bobbin()

    def calculating_bobbin(self):
        number_full_bobbin = self.length_strands // self.volume_bobbin  # количество полных катушек в расчете на 1 прядь
        volume_half_bobbin = round(self.length_strands % self.volume_bobbin, 2)  # меди на неполной катушки на 1 прядь

        self.full_bobbin = int(number_full_bobbin), volume_half_bobbin, int(int(number_full_bobbin) > 0)

    @property
    def time_setup(self):
        return self.__time_setup

    @time_setup.setter
    def time_setup(self, value):
        self.__time_setup = value

    def __str__(self) -> str:
        # return "{} | {} | {} | {} | {} | {} | {} | {} | {}".format(
        #     self.id, self.account_number, self.num_group, self.order.release_date, self.length_strands, self.group,
        #     self.full_bobbin, self.time_on_mult, self.order.time_on_streng
        # )

        return "{} | {} | {} | {}".format(
            self.account_number, self.order.release_date, self.group,
            self.full_bobbin, self.time_on_mult_1_basket
        )

    def __repr__(self):
        return "'%s'" % self.account_number

    def match(self, **kwargs):
        return all(getattr(self, key) == val for (key, val) in kwargs.items())


class Basket:
    """
    Корзина для подачи на мультик. Класс создается когда заказы с мультика израсходуют суммарно 8 корзин.
    Класс передается в очередь на волочилку.
    """

    def __init__(self, orders=None, sum_basket=0):
        """
        Создание корзины. Когда будет несколько заказов в корзинах, тогда используются значения параметров по умолчанию.
        Если один заказ тратит 8 корзин, тогда используются переданные параметры
        :param orders: None, если много заказов. Не None, если 1 заказ
        :param sum_basket: 0, если много заказов. 8, если 1 заказ
        """
        if orders is None:
            orders = []
        self.time_work = 0
        self.orders: [MultivareTask] = orders
        self.diameter = d_mult
        self.len_basket = KM_IN_1_BASKET * 8
        self.sum_basket = sum_basket
        self.set_time_work()

    def set_time_work(self):
        """
        Устанавливается время траты 8 корзин.
        1. Если заказов 0, значит экземпляр корзины только что создан и будет набиваться заказами
        2. Иначе заказ полностью тратит 8 корзин и время считается из его параметров без времени перенастройки, т.к. в таком случае уже будет заказ ранее, где учтено это время
        :return: время, за которое потратится 8 корзин, если 0, тогда время будет увеличиваться по мере добавления заказов
        """
        if len(self.orders) == 0:
            self.time_work = 0
        else:
            self.time_work = self.orders[0].time_on_mult_1_basket * self.sum_basket

    def append(self, order: MultivareTask, num_basket=None, use_time_setup=True):
        """
        1. Если заказ полностью подходит по вместимости корзины, то берем время и длину из заказа
        2. Если заказ не влазит в текущую корзину, то в одну корзину добавляем, что остается до восьми целых,
        а в следующую все что осталось от этого заказа
        :param use_time_setup: True когда заказ сидит только в одной корзине. False, когда заказ встречается уже во второй раз, чтобы не учитывать второй раз время перенастройки
        :param order: Заказ на мультик
        :param num_basket: None, если заказ полностью влез в корзину. Не None, если часть заказа будет в двух разны корзинах
        :return:
        """
        self.orders.append(order)
        if num_basket is None:
            # Тут берем траты корзины из заказа
            self.time_work += order.time_on_mult_1_basket * order.num_basket[1] + order.time_setup
            self.sum_basket += order.num_basket[1]
        else:
            # Тут берем траты корзины из параметра
            self.time_work += order.time_on_mult_1_basket * num_basket + (order.time_setup if use_time_setup else 0)
            self.sum_basket += num_basket
        # queue_multivare.find_order(account_number=order.account_number)

    def __repr__(self):
        return 'Корзина (Время работы заказов = {}ч. {}мин.; Длина {}): {}'.format(str(self.time_work // 60),
                                                                                   str(round(
                                                                                       self.time_work % 60,
                                                                                       2)), self.sum_basket,
                                                                                   self.orders.__repr__())


class QueueMultivare:
    """
    Оптимальная очередь на мультике. С методами поиска любого заказа по заданным параметрам
    """

    rest_basket: float = 0.0
    rest_orders: [MultivareTask] = []

    def __init__(self):
        self.__queue: [MultivareTask] = []

    @property
    def queue(self):
        return self.__queue

    @queue.setter
    def queue(self, orders):
        self.__queue = orders

    def __add__(self, other):
        self.__queue.append(other)

    def find_order(self, **kwargs):
        return next(self.__iter_order(**kwargs))

    def all_orders(self, **kwargs):
        return list(self.__iter_order(**kwargs))

    def __iter_order(self, **kwargs):
        return (order for order in self.__queue if order.match(**kwargs))

    @staticmethod
    def calculate_setup_time_multivare(previous_order, order):
        """
        Функция для расчета времени перенастройки между заказами мультика.
        Считается время перенастройки и смены катушки между заказами
        Не учитывается добавление катушки, если она заполнена
        ??? После определения оптимального варианта будет пересчет через чеклист мультика
        :param previous_order:
        :param order:
        :return:
        """

        total_setup_time = 0

        if previous_order is not None:

            change = False

            """
                1 ПРОВЕРКА -- Разность диаметров
            """

            # меньше диаметр - больше фильер
            if previous_order.spin > order.spin:
                removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
                total_setup_time += removed_spin * MultivareMachine.REMOVED_SPIN  # Время на снятие фильер
                total_setup_time += MultivareMachine.INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер
                change = True
            # больше диаметр - меньше фильер
            elif previous_order.spin < order.spin:
                removed_spin = 1  # снимаем последнюю
                total_setup_time += removed_spin * MultivareMachine.REMOVED_SPIN  # время на снятие фильер
                total_setup_time += MultivareMachine.INSERT_SPIN * (
                        order.spin - (
                        previous_order.spin - 1)) * order.wires_in_sliver  # время на установку фильер +1, потому 1 уже снята tt
                change = True

            """
                2 ПРОВЕРКА -- Разность проволочек
            """

            dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

            if previous_order.wires_in_sliver < order.wires_in_sliver:
                # Надо протянуть новые проволочки через все фильеры на новом заказе
                total_setup_time += dif_wire * order.spin * MultivareMachine.CHANGE_WIRE + MultivareMachine.STRETCHING_WIRE
                change = True
            elif previous_order.wires_in_sliver > order.wires_in_sliver:
                # Надо снять проволочки со всех фильер previous_order
                total_setup_time += dif_wire * previous_order.spin * MultivareMachine.CHANGE_WIRE
                change = True

            # после каждого заказа будет смена заказа
            # if change:
            #     # Если было любое изменение, то надо сменить катушку
            #     total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

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
                temp_matrix2.append(QueueMultivare.calculate_setup_time_multivare(order1, order2))
            temp_matrix1.append(temp_matrix2)
        return temp_matrix1

    @staticmethod
    def get_total_time(time_on_multivare, indices):
        """
        Считается время перенастроек между заказов для текущей очереди
        :param time_on_multivare: время перенастроек для каждого заказа с каждым
        :param indices: текущий индивид (очередь).
        :return: Всё время перенастроек для текущей очереди
        """

        time = 0

        # время между каждой парой заказов
        for i in range(len(indices) - 1):
            time += time_on_multivare[indices[i]][indices[i + 1]]

        return time,

    def setting_time_setup(self):
        """
        Определяем время настройки заказов на мультике.
        :return:
        """

        for i in range(len(self.__queue)):

            # пропускаем первый индекс, т.к у него нет время на перенастройку
            if i == 0:
                continue

            self.__queue[i].time_setup = QueueMultivare.calculate_setup_time_multivare(self.__queue[i - 1],
                                                                                       self.__queue[i])

    def calculating_basket(self):
        """
        Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
        если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
        :return:
        """

        sum_basket: int = 0
        temp_basket: Basket = Basket()
        for order in self.__queue:

            # Если со следующим заказом получается меньше 8 корзин, но он занимает сам по себе больше 8 корзин
            if order.num_basket[0] > 0 and (sum_basket + order.num_basket[1]) <= 8:
                rest_basket = 8 - sum_basket  # сколько нужно до 8 корзин
                temp_num_basket = (order.num_basket[0] - 1, order.num_basket[1] + (8 - rest_basket))
                # распределяем полные корзины -> (2 (полные корзины), 5.47 (неполные корзины) -> (1, 5.47) -> (1, 13.47 + (8 - rest_basket))
                # Добавляем такой заказ последним и начинаем новые корзины, потому что после него пойдут корзины только для этого заказа
                sum_basket += rest_basket
                temp_basket.append(order, rest_basket)
                Dragger.queue_dragger_new_dragger.append(Dragger.TaskForDragger(temp_basket))

                for _ in range(temp_num_basket[0]):
                    Dragger.queue_dragger_new_dragger.append(Dragger.TaskForDragger(Basket([order], 8)))

                sum_basket = 0
                temp_basket: Basket = Basket()
                sum_basket += temp_num_basket[1]
                temp_basket.append(order, num_basket=temp_num_basket[1], use_time_setup=False)

            # Если со следующим заказом получается больше 8 корзин
            elif (sum_basket + order.num_basket[1]) > 8:
                # Прибавляем так, чтобы стало 8 и добавляем время изготовления этой части корзины
                rest_basket = 8 - sum_basket  # сколько нужно до 8 корзин
                temp_basket.append(order, rest_basket)
                Dragger.queue_dragger_new_dragger.append(Dragger.TaskForDragger(temp_basket))

                # Если заказ на больше 8 корзин, то между корзин будут корзины с 1 этим заказом
                for _ in range(order.num_basket[0]):
                    Dragger.queue_dragger_new_dragger.append(Dragger.TaskForDragger(Basket([order], 8)))

                # начинаем новую корзину и добавляем в нее остаток текущего заказа
                temp_basket: Basket = Basket()
                sum_basket = order.num_basket[1] - rest_basket  # сколько корзин нужно
                temp_basket.append(order, sum_basket, False)
                # Переходим к следующему заказу, т.к. этот полностью исчерпан
            else:
                sum_basket += order.num_basket[1]
                temp_basket.append(order)
        else:
            if len(temp_basket.orders) > 0:
                # Dragger.queue_dragger.append(Dragger.TaskForDragger(temp_basket))
                QueueMultivare.rest_basket += sum_basket
                QueueMultivare.rest_orders = temp_basket


class CheckListMultivare:
    """
    Катушки на мультике. Наматываем кабель с мультика на катушки и выводим в эксель
    """

    def __init__(self):
        self.bobbins: [Bobbin] = []
        # self.sum_time: float = 0

    def append(self, bobbin):
        self.bobbins.append(bobbin)

    def clear(self):
        self.bobbins.clear()

    def __add__(self, other):
        self.bobbins.extend(other.bobbins)

    def get_sum_time(self):
        return sum(bobbin.time_on_mult for bobbin in self.bobbins)

    @staticmethod
    def sort_date(bobbin):
        return bobbin.date_first_order

    @staticmethod
    def sort_num(bobbin):
        return bobbin.number

    def calculate_time_setup(self):

        previous_order = None
        total_setup_time = 0

        for bobbin in self.bobbins:

            for order in bobbin.orders:

                if previous_order is not None:

                    """
                        1 ПРОВЕРКА -- Разность фильер
                    """

                    # меньше диаметр - больше фильер
                    if previous_order.spin > order.spin:
                        removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
                        total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
                        total_setup_time += INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер

                    # больше диаметр - меньше фильер
                    elif previous_order.spin < order.spin:
                        removed_spin = 1  # снимаем последнюю
                        total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
                        total_setup_time += INSERT_SPIN * (order.spin - (
                                previous_order.spin - 1)) * order.wires_in_sliver  # время на установку фильер +1, потому 1 уже снята tt

                    """
                        2 ПРОВЕРКА -- Разность проволочек
                    """

                    dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

                    if previous_order.wires_in_sliver < order.wires_in_sliver:
                        # Надо протянуть новые проволочки через все фильеры на новом заказе
                        total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
                    elif previous_order.wires_in_sliver > order.wires_in_sliver:
                        # Надо снять проволочки со всех фильер previous_order
                        total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE

                previous_order = order
            else:
                # После окончания цикла переход на следующую катушку
                total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

        return total_setup_time

    def output_in_excel(self):
        """
            0 - как есть
            1 - по дате
            :return:
            """

        # self.bobbins.sort(key=self.sort_num)

        print('Выберите сортировку:')
        print('0 - как есть')
        print('1 - по дате')
        k = int(input())
        if k == 1:
            self.bobbins = sorted(self.bobbins, key=self.sort_date)

        existing_file = 'excel/group_with_date.xlsx' if k else 'excel/group_without_date.xlsx'

        header = ['Номер группы', 'Номер катушки', 'Номер счета', 'Группа', 'Намотка', 'Max намотка', 'Дата']

        data = []
        for bobbin in self.bobbins:
            # Инициализируем пустой список для хранения данных
            # Извлекаем данные из PrettyTable и добавляем их в список
            i = 0
            for order in bobbin.orders:
                if i == 0:
                    data.append(
                        [order.num_group, bobbin.number, order.account_number, order.group,
                         bobbin.volume, bobbin.max_volume, bobbin.date_first_order]
                    )
                    i += 1
                else:
                    data.append(
                        [order.num_group, bobbin.number, order.account_number, order.group, '', '', '']
                    )

        df = pd.DataFrame(data, columns=header, index=None)

        mode = "w" if os.path.exists(existing_file) else "a"

        with ExcelWriter(existing_file, mode=mode, engine="openpyxl") as writer:
            df.to_excel(writer)


queue_multivare = QueueMultivare()
check_list_multik = CheckListMultivare()


class Bobbin:
    count = 0

    def __init__(self, volume, max_volume, date, order):
        Bobbin.count += 1
        self.number = Bobbin.count
        self.max_volume = max_volume
        self.date_first_order = date
        self.volume: float = 0
        self.orders: [MultivareTask] = []
        self.time_on_mult: float = 0
        self.add(volume, order)

    def add(self, volume, order):
        if volume != 0 and order is not None:
            self.volume += volume
            self.orders.append(order)
            self.time_on_mult += order.time_on_mult
