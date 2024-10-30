import weakref
from prettytable import PrettyTable
import re
from gosts import GOSTS
import Оборудование.Multivare as Multivare
import Оборудование.Dragger as Dragger

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

# main_table = PrettyTable(
#     ["Номер счета", "Марка", "Дата выпуска", "Длина кабеля, км", "Километраж", "Время на мультике"]
# )
#
# second_param_table = PrettyTable(
#     ["Длина кабеля, км", "Количество жил", "Диаметр проволоки на волочении, мм",
#      "Кол-во стренг", "Кол-во прядей", "Кол-во проволок в пряди", "Кол-во прядей доп",
#      "Кол-во проволок доп", "Тип барабана", "Километраж", "Время на мультике"]
# )


def converting_indexes_to_numbers(indexes: [int], orders: [Multivare.TaskForMultik]):
    """
    Преобразует список индексов заказов в список номеров и ссылок
    :param indexes: список индексов заказов
    :param orders: список заказов элементов класса
    :return: (список номеров заказа, список ссылок на заказы)
    """
    return list(map(lambda i: orders[i], indexes))


class OrderMeta(type):
    """
    Метакласс для отслеживания всех экземпляров класса Order.
    """
    _instances = weakref.WeakSet()

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(instance)
        return instance

    @classmethod
    def get_all_instances(cls):
        return list(cls._instances)


class Order(metaclass=OrderMeta):
    """
    Класс содержит все не вычисляемые параметры по кабелю. По факту просто справочник содержащий все переменные по заказу.
    Далее будет разбиваться по заданиям на оборудования, куда пойдут определенные переменные.
    """

    def __init__(
            self, IDZak, account_number, mark, release_date, order_length, number_of_veins, diameter, number_of_strands,
            number_of_sliver, wires_in_sliver, number_of_sliver_extra, wires_in_sliver_extra, number_of_veins_plus,
            diameter_plus, number_of_strands_plus, number_of_sliver_plus, wires_in_sliver_plus,
            number_of_sliver_extra_plus, wires_in_sliver_extra_plus, number_of_veins_support, diameter_support,
            number_of_strands_support, number_of_sliver_support, wires_in_sliver_support,
            number_of_sliver_extra_support,
            wires_in_sliver_extra_support, type_bobbin, volume_bobbin, time_on_dragger, time_on_multivare,
            time_on_streng):
        self.IDZak = IDZak
        self.account_number = account_number
        self.mark = Mark(mark)
        self.release_date = release_date
        self.order_length = order_length
        self.number_of_veins = number_of_veins
        self.diameter = diameter
        self.number_of_strands = number_of_strands
        self.number_of_sliver = number_of_sliver
        self.wires_in_sliver = wires_in_sliver
        self.number_of_sliver_extra = number_of_sliver_extra
        self.wires_in_sliver_extra = wires_in_sliver_extra
        self.number_of_veins_plus = number_of_veins_plus
        self.diameter_plus = diameter_plus
        self.number_of_strands_plus = number_of_strands_plus
        self.number_of_sliver_plus = number_of_sliver_plus
        self.wires_in_sliver_plus = wires_in_sliver_plus
        self.number_of_sliver_extra_plus = number_of_sliver_extra_plus
        self.wires_in_sliver_extra_plus = wires_in_sliver_extra_plus
        self.number_of_veins_support = number_of_veins_support
        self.diameter_support = diameter_support
        self.number_of_strands_support = number_of_strands_support
        self.number_of_sliver_support = number_of_sliver_support
        self.wires_in_sliver_support = wires_in_sliver_support
        self.number_of_sliver_extra_support = number_of_sliver_extra_support
        self.wires_in_sliver_extra_support = wires_in_sliver_extra_support
        self.type_bobbin = type_bobbin
        self.volume_bobbin = volume_bobbin
        self.time_on_dragger = time_on_dragger
        self.time_on_multivare = time_on_multivare
        self.time_on_streng = time_on_streng
        self.operation_sequence = []
        self.task = self.set_task()

    def set_task(self):
        """
        Создаем задания на оборудования, разбивая кабель на несколько составляющих. Если в кабеле есть дополнительные жилы,
        то каждая дополнительная жила в задании будет восприниматься как отдельный заказ с аналогичным номером с добавлением
        +/е/s
        :return: массив, элементы которого задания на различные оборудования по техцепочке
        """
        task = []

        # Если заказ пойдет на мультик, то у него не должно быть задания на волочилку, т.к. для таких заказов заданием будет являться корзина
        if self.time_on_dragger and not self.time_on_multivare:
            # task.append(self.set_task_for_dragger())
            self.operation_sequence.append('WireDrawing')
        if self.time_on_multivare:
            # task.extend(self.set_task_for_multivare())
            self.operation_sequence.append('Multivare')

        return task

    def set_task_for_dragger(self):
        """
        Заводим Задание на волочилку и добавляем задание в очередь. Тут очередь будет еще не в оптимальном порядке
        :return:
        """
        return Dragger.TaskForDragger(self)

    def set_task_for_multivare(self):
        task = [Multivare.TaskForMultik(self, self.diameter, self.number_of_veins, self.number_of_strands,
                                        self.number_of_sliver, self.wires_in_sliver, '')]
        if self.number_of_sliver_extra:
            task.append([Multivare.TaskForMultik(self, self.diameter, self.number_of_veins, self.wires_in_sliver_extra,
                                                 self.number_of_sliver_extra,
                                                 self.wires_in_sliver_extra, 'e')])

        if self.mark.cable_parameters.get('Тип') == 'Плюсовой':
            task.append(Multivare.TaskForMultik(self, self.diameter_plus, self.number_of_veins_plus,
                                                self.number_of_strands_plus,
                                                self.number_of_sliver_plus,
                                                self.wires_in_sliver_plus, '+'))

            if self.number_of_sliver_extra_plus:
                task.append(
                    [Multivare.TaskForMultik(self, self.diameter_plus, self.number_of_veins_plus,
                                             self.number_of_strands_plus,
                                             self.number_of_sliver_extra_plus,
                                             self.wires_in_sliver_extra_plus, 'e+')])

        if self.mark.cable_parameters.get('Тип') == 'Вспомогательный':
            task.append(Multivare.TaskForMultik(self, self.diameter, self.number_of_veins_support,
                                                self.number_of_strands_support,
                                                self.number_of_sliver_support,
                                                self.wires_in_sliver_support, 's'))
            if self.number_of_sliver_extra_support:
                task.append(
                    Multivare.TaskForMultik(self, self.diameter, self.number_of_veins_support,
                                            self.number_of_strands_support,
                                            self.number_of_sliver_extra_support,
                                            self.wires_in_sliver_extra_support, 'es'))

        return task

    def __repr__(self) -> str:
        return "{} | {} | {} | {} | {}".format(
            self.account_number, self.mark.mark, self.mark.cable_parameters, self.release_date, self.order_length
        )


class Mark:
    """
    Класс, описывающий марку кабеля, содержит расшифровку
    """

    def __init__(self, mark):
        self.mark: str = mark
        self.cable_parameters = {}
        self.type_definition(mark)

    def type_definition(self, mark):
        """
        Берем каждый гост из справочника и проверяем марку на каждый патерн.
        После того как найдем подходящий гост вызываем cable_decryption, передаем найденный результат и гост
        """
        for gosts in GOSTS.keys():
            res = re.search(GOSTS[gosts]['pattern'], mark, flags=0)

            if res is not None:
                self.cable_decryption(res, gosts)
                break
        # else:
        # print(mark, 'не определена')

    def cable_decryption(self, result, gosts):
        """
        Забираем из справочника гостов все параметры по совпавшему госту (gosts).
        Затем выводим все параметры по совпавшим группам и записываем в справочник класса
        """
        name_groups = GOSTS[gosts]['param']

        for group in name_groups:
            if result.group(group) != '' and result.group(group) is not None:
                self.cable_parameters[name_groups[group]] = result.group(group)

        self.cable_parameters['Тип'] = self.set_type(self.mark)

    @staticmethod
    def set_type(mark: str):
        if mark.count('+') == 0:
            return 'Не плюсовой'
        elif mark.count('+') == 1:
            return 'Плюсовой'
        else:
            return 'Вспомогательный'
