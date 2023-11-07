from prettytable import PrettyTable

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
dict_key_group = {
}

# A - IDZak
# B - Номер счета
# C - Марка
# D - Дата выпуска по заказу
# E - Количество километров в производство
# F - Количество жил
# G - Перед мультиком -> d_mult = 2.08
# H - Диаметр проволоки
# I - Количество стренг
# J - Кол-во прядей
# K - Кол-во проволок в пряди
# L - Кол-во прядей доп
# M - Кол-во проволок доп
# N - Вид барабана
# O - Количество заправок
# P - Километраж масса VS Длина
# Q - Время на мультике

main_table = PrettyTable(
    ["Номер счета", "Марка", "Дата выпуска", "Длина кабеля, км", "Километраж", "Время на мультике"])

second_param_table = PrettyTable(["Длина кабеля, км", "Количество жил", "Диаметр проволоки на волочении, мм",
                                  "Кол-во стренг", "Кол-во прядей", "Кол-во проволок в пряди", "Кол-во прядей доп",
                                  "Кол-во проволок доп", "Тип барабана", "Километраж", "Время на мультике"])

# Добавить в таблицу тип барабана, количество полных барабанов, вместимость полного барабана, остаток на последнем
# барабане, и разбить реквизит "Всего проволочек в 1 стренге, шт." на "количество прядей, шт.", "количество проволок в
# одной пряди, шт."

d_mult = 2.08


class Bobbin:

    def __init__(self, volume, date):
        self.volume = volume
        self.orders = [Order]
        self.date_first_order = date

    def add(self, volume):
        self.volume += volume

    def append_order(self, order):
        self.orders.append(order)

class Order:

    def __init__(self, account_number, mark, release_date, order_length, number_of_veins, diameter, number_of_strands,
                 number_of_sliver, wires_in_sliver, number_of_sliver_extra, wires_in_sliver_extra, type_bobbin,
                 volume_bobbin, time_on_mult):
        self.length_strands = 0
        self.full_bobbin = ()
        self.length_piece = 0
        self.spin = 0
        self.num_group = None
        self.group = ()
        self.total_length_delays = 0
        self.account_number = account_number
        self.mark = mark
        self.release_date = release_date
        self.order_length = order_length
        self.number_of_veins = number_of_veins
        self.diameter = diameter
        self.number_of_strands = number_of_strands
        self.number_of_sliver = number_of_sliver
        self.wires_in_sliver = wires_in_sliver
        self.number_of_sliver_extra = number_of_sliver_extra
        self.wires_in_sliver_extra = wires_in_sliver_extra
        self.type_bobbin = type_bobbin
        self.volume_bobbin = volume_bobbin
        self.time_on_mult = time_on_mult
        self.counting_spinners()
        self.set_group()
        self.calculating_length()

    def set_group(self) -> None:
        """
        Устанавливаем группу и номер группы для заказа
        """
        key = (self.diameter, self.number_of_sliver, self.wires_in_sliver, self.number_of_sliver_extra,
               self.wires_in_sliver_extra, self.type_bobbin)

        if dict_key_group.get(key) is None:
            dict_key_group[key] = len(dict_key_group)

        self.group = key
        self.num_group = dict_key_group[key]

    def counting_spinners(self) -> None:
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        """

        self.spin = dictionary_spinners[min(dictionary_spinners, key=lambda x: abs(self.diameter - x))]

    def calculating_bobbin(self):
        sliver = self.number_of_sliver + self.number_of_sliver_extra

        number_full_bobbin = self.length_strands // self.volume_bobbin  # количество полных катушек в расчете на 1 прядь
        volume_half_bobbin = round(self.length_strands % self.volume_bobbin, 2)  # меди на неполной катушки на 1 прядь

        all_full_bobbin = number_full_bobbin * sliver
        all_half_bobbin = sliver  # = количеству прядей, т.к. последняя заправка

        # res = [[volume_bobbin for _ in range(sliver)] for _ in range(int(number_full_bobbin))]
        # res.append([volume_half_bobbin for _ in range(sliver)])

        self.full_bobbin = int(number_full_bobbin), volume_half_bobbin

    def calculating_length(self):
        # суммарная длина проволочек

        self.total_length_delays = ((
                                            self.number_of_sliver * self.wires_in_sliver + self.number_of_sliver_extra * self.wires_in_sliver_extra)
                                    * self.number_of_strands * self.number_of_veins * self.order_length)

        self.length_piece = round(self.total_length_delays * (self.diameter ** 2 / d_mult ** 2), 3)

        # длина заказа в расчете на одну прядь (весь заказ это length_strands *
        # (number_of_sliver + number_of_sliver_extra))
        self.length_strands = round((self.order_length * self.number_of_veins * self.number_of_strands), 2)

        # подсчет барабанов
        self.calculating_bobbin()

    def __str__(self) -> str:
        return "{} | {} | {} | {} | {} | {}".format(self.account_number, self.mark, self.release_date,
                                                    self.order_length, self.num_group, self.spin)
