from consts import *
import inspect
from pprint import pprint

dictionary_spinners = {
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

dict_key_group = {}


class TaskForMultik:
    """
    Задание на мультик хранит в переменной класса хранит все заказы в массиве, их можно будет найти по IDZak

    """
    orders = []

    def __init__(self, order, diameter, number_of_veins, number_of_strands, number_of_sliver, wires_in_sliver,
                 number_of_sliver_extra, wires_in_sliver_extra, type):
        TaskForMultik.orders.append(self)
        self.order = order
        self.volume_bobbin = order.volume_bobbin
        self.IDZak = order.IDZak
        self.account_number = order.account_number + type
        self.diameter = diameter
        self.number_of_sliver = number_of_sliver
        self.wires_in_sliver = wires_in_sliver
        self.number_of_veins = number_of_veins
        self.number_of_strands = number_of_strands
        self.number_of_sliver_extra = number_of_sliver_extra
        self.wires_in_sliver_extra = wires_in_sliver_extra
        self.group = ()
        self.num_group = 0
        self.spin = 0
        self.total_length_delays = 0
        self.length_piece = 0
        self.length_strands = 0
        self.full_bobbin = ()
        self.time_on_mult = order.time_on_mult
        self.counting_spinners()
        self.set_group()
        self.calculating_length()

    def set_group(self) -> None:
        """
        Устанавливаем группу и номер группы для заказа
        """
        # key = (self.spin, self.number_of_sliver, self.wires_in_sliver, self.order.type_bobbin)

        # группы без количества жил хз как там катушки меняются
        key = (self.spin, self.wires_in_sliver, self.order.type_bobbin)

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

        self.total_length_delays = ((self.number_of_sliver * self.wires_in_sliver + self.number_of_sliver_extra *
                                     self.wires_in_sliver_extra) * self.number_of_strands * self.number_of_veins * self.order.order_length)

        self.length_piece = round(self.total_length_delays * (self.diameter ** 2 / d_mult ** 2), 3)

        # длина заказа в расчете на одну прядь (весь заказ это length_strands *
        # (number_of_sliver + number_of_sliver_extra))
        self.length_strands = round((self.order.order_length * self.number_of_veins * self.number_of_strands), 2)

        # подсчет барабанов
        self.calculating_bobbin()

    def calculating_bobbin(self):
        number_full_bobbin = self.length_strands // self.order.volume_bobbin  # количество полных катушек в расчете на 1 прядь
        volume_half_bobbin = round(self.length_strands % self.order.volume_bobbin,
                                   2)  # меди на неполной катушки на 1 прядь

        self.full_bobbin = int(number_full_bobbin), volume_half_bobbin, int(int(number_full_bobbin) > 0)

    def __str__(self) -> str:
        return "{} | {} | {} | {} | {}".format(
            self.account_number, self.spin, self.order.release_date, self.length_strands, self.group
        )


class Check_List:
    """
    Катушки на мультике. Наматываем кабель с мультика на катушки и выводим в эксель
    """

    def __init__(self):
        self.bobbins: [Bobbin] = []
        # self.sum_time: float = 0

    def append(self, bobbin):
        self.bobbins.append(bobbin)

    def __add__(self, other):
        self.bobbins.extend(other.bobbins)

    def get_sum_time(self):
        return sum(bobbin.time_on_mult for bobbin in self.bobbins)

    @staticmethod
    def sort_date(bobbin):
        return bobbin.date_first_order

    def output_in_excel(self):
        """
        0 - как есть
        1 - по дате
        :return:
        """

        print('Выберите сортировку:')
        print('0 - как есть')
        print('1 - по дате')
        k = int(input())
        if k == 1:
            self.bobbins = sorted(self.bobbins, key=self.sort_date)

        existing_file = 'excel/group_with_date.xlsx' if k else 'excel/group_without_date.xlsx'

        header = ['Номер группы', 'Номер катушки', 'Номер счета', 'Намотка', 'Max намотка', 'Дата']

        data = []
        for bobbin in self.bobbins:
            # Инициализируем пустой список для хранения данных
            # Извлекаем данные из PrettyTable и добавляем их в список
            i = 0
            for order in bobbin.orders:
                if i == 0:
                    data.append(
                        [order.num_group, bobbin.number, order.account_number,
                         bobbin.volume, bobbin.max_volume, bobbin.date_first_order]
                    )
                    i += 1
                else:
                    data.append(
                        [order.num_group, bobbin.number, order.account_number, '', '', '']
                    )

        df = pd.DataFrame(data, columns=header, index=None)

        mode = "w" if os.path.exists(existing_file) else "a"

        with ExcelWriter(existing_file, mode=mode, engine="openpyxl") as writer:
            df.to_excel(writer)


check_list_multik = Check_List()


class Bobbin:
    count = 0

    def __init__(self, volume, max_volume, date, order):
        Bobbin.count += 1
        self.number = Bobbin.count
        self.max_volume = max_volume
        self.date_first_order = date
        self.volume: float = 0
        self.orders: [Order] = []
        self.time_on_mult: float = 0
        self.add(volume, order)

    def add(self, volume, order):
        if volume != 0 and order is not None:
            self.volume += volume
            self.orders.append(order)
            self.time_on_mult += order.time_on_mult
