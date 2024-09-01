import os
from pandas import ExcelWriter
import pandas as pd
import Оборудование.Dragger as Dragger

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

pi = 3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679821480865132823066470938446095

dict_key_group = {}


class TaskForMultik:
    """
    Задание на мультик хранит в переменной класса хранит все заказы в массиве, их можно будет найти по IDZak
    """
    orders = []

    def __init__(self, order, diameter, number_of_veins, number_of_strands, number_of_sliver, wires_in_sliver, type):
        TaskForMultik.orders.append(self)
        self.order = order

        self.id = len(TaskForMultik.orders)

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
        self.time_on_mult = order.time_on_multivare
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

        self.spin = dictionary_spinners[min(dictionary_spinners, key=lambda x: abs(self.order.diameter - x))]

    def calculating_length(self):
        # суммарная длина проволочек

        self.total_weight_delays = ((
                                                self.number_of_sliver * self.wires_in_sliver) * self.number_of_strands * self.number_of_veins * self.order.order_length) * pi * 8.89 * (
                                               self.diameter ** 2) * 0.25
        self.length_piece = round(self.total_weight_delays * (self.diameter ** 2 / d_mult ** 2), 3)

        # 0 - сколько корзин по 8 штук нужно, если заказ очень большой и требуется много корзин
        # 1 - сколько корзин еще заполнится (набирается число до 8)
        self.num_basket = (int(self.total_weight_delays / self.wires_in_sliver / KM_IN_1_BASKET // 8),
                           self.total_weight_delays / self.wires_in_sliver / KM_IN_1_BASKET % 8)

        # длина заказа в расчете на одну прядь (весь заказ это length_strands *
        # (number_of_sliver + number_of_sliver_extra))
        self.length_strands = round((self.order.order_length * self.number_of_veins * self.number_of_strands), 2)

        # подсчет барабанов
        self.calculating_bobbin()

    def calculating_bobbin(self):
        number_full_bobbin = self.length_strands // self.volume_bobbin  # количество полных катушек в расчете на 1 прядь
        volume_half_bobbin = round(self.length_strands % self.volume_bobbin, 2)  # меди на неполной катушки на 1 прядь

        self.full_bobbin = int(number_full_bobbin), volume_half_bobbin, int(int(number_full_bobbin) > 0)

    def __str__(self) -> str:
        # return "{} | {} | {} | {} | {} | {} | {} | {} | {}".format(
        #     self.id, self.account_number, self.num_group, self.order.release_date, self.length_strands, self.group,
        #     self.full_bobbin, self.time_on_mult, self.order.time_on_streng
        # )

        return "{} | {} | {} | {} | {}".format(
            self.id, self.account_number, self.order.release_date, self.group,
            self.full_bobbin, self.time_on_mult
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
        if orders is None:
            orders = []
        self.orders: [TaskForMultik] = orders
        self.diameter_on_exit = d_mult
        self.len_basket = KM_IN_1_BASKET * 8
        self.sum_basket = sum_basket
        self.time_work = 0

    def append(self, order: TaskForMultik):
        self.orders.append(order)
        self.time_work += order.time_on_mult
        self.sum_basket += order.num_basket[1]
        # queue_multivare.find_order(account_number=order.account_number)

    def __str__(self):
        return '{} \n'.format(self.orders)


class QueueMultivare:
    """
    Оптимальная очередь на мультике. С методами поиска любого заказа по заданным параметрам
    """

    rest_baskt: float = 0.0

    def __init__(self):
        self.__queue: [TaskForMultik] = []

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

    def calculating_basket(self):
        """
        Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
        если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
        :return:
        """

        sum_basket: int = 0
        temp_basket: Basket = Basket()
        for order in self.__queue:

            sum_basket += order.num_basket[1]
            temp_basket.append(order)

            for _ in range(order.num_basket[0]):
                Dragger.queue_dragger.orders.append(Basket([order], 8))

            if sum_basket > 8:
                Dragger.queue_dragger.orders.append(temp_basket)
                temp_basket: Basket = Basket()
                sum_basket = 0
        else:
            if len(temp_basket.orders) > 0:
                Dragger.queue_dragger.orders.append(temp_basket)
                QueueMultivare.rest_baskt += sum_basket


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
        self.orders: [TaskForMultik] = []
        self.time_on_mult: float = 0
        self.add(volume, order)

    def add(self, volume, order):
        if volume != 0 and order is not None:
            self.volume += volume
            self.orders.append(order)
            self.time_on_mult += order.time_on_mult
