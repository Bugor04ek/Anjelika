import weakref
from prettytable import PrettyTable
import re
from gosts import GOSTS
import Оборудование.Multivare as Multivare
import Оборудование.Dragger as Dragger
from Оборудование.Equipments import TaskMeta

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


def converting_indexes_to_numbers(indexes: [int], orders: [Multivare.MultivareTask]):
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


class Task(metaclass=TaskMeta):
    """
    Класс для описания конкретного задания на операцию для части кабеля (например, основного, плюсового или вспомогательного).
    """

    def __init__(self, order, operation_sequence, equipment_type):
        self.order = order  # Основной заказ, к которому относится задание
        self.operation_sequence = operation_sequence  # Список операций, которые должен пройти данный элемент
        self.current_operation_index = 0  # Указатель на текущую операцию
        self.equipment_type = equipment_type  # Тип оборудования (например, "WireDrawing" или "Multivare")
        self.equipment = None  # Оборудование не указано при инициализации

    def next_operation(self):
        """
        Переход к следующей операции в цепочке.
        """
        if self.current_operation_index < len(self.operation_sequence) - 1:
            self.current_operation_index += 1
            return self.operation_sequence[self.current_operation_index]
        return None  # Завершение операций

    def assign_equipment(self, equipment):
        if equipment.equipment_type == self.equipment_type:
            self.equipment = equipment

    def assign_tasks_to_equipment(tasks, available_equipments):
        for task in tasks:
            suitable_equipments = [eq for eq in available_equipments if eq.is_suitable(task.material, task.diameter)]
            if suitable_equipments:
                equipment = random.choice(suitable_equipments)
                task.assign_equipment(equipment)

    def __repr__(self):
        return f"OrderTask(part_type={self.part_type}, current_operation={self.operation_sequence[self.current_operation_index]})"


class Order(metaclass=OrderMeta):
    """
    Класс содержит все не вычисляемые параметры по кабелю. По факту просто справочник содержащий все переменные по заказу.
    Далее будет разбиваться по заданиям на оборудования, куда пойдут определенные переменные.
    """

    # def __init__(
    #         self, IDZak, account_number, mark, release_date, order_length, number_of_veins, diameter, number_of_strands,
    #         number_of_sliver, wires_in_sliver, number_of_sliver_extra, wires_in_sliver_extra, number_of_veins_plus,
    #         diameter_plus, number_of_strands_plus, number_of_sliver_plus, wires_in_sliver_plus,
    #         number_of_sliver_extra_plus, wires_in_sliver_extra_plus, number_of_veins_support, diameter_support,
    #         number_of_strands_support, number_of_sliver_support, wires_in_sliver_support,
    #         number_of_sliver_extra_support,
    #         wires_in_sliver_extra_support, type_bobbin, volume_bobbin, time_on_dragger, time_on_multivare,
    #         time_on_streng):
    #
    #     self.IDZak = IDZak
    #     self.account_number = account_number
    #     self.mark = Mark(mark)
    #     self.release_date = release_date
    #     self.order_length = order_length
    #     self.number_of_veins = number_of_veins
    #     self.diameter = diameter
    #     self.number_of_strands = number_of_strands
    #     self.number_of_sliver = number_of_sliver
    #     self.wires_in_sliver = wires_in_sliver
    #     self.number_of_sliver_extra = number_of_sliver_extra
    #     self.wires_in_sliver_extra = wires_in_sliver_extra
    #     self.number_of_veins_plus = number_of_veins_plus
    #     self.diameter_plus = diameter_plus
    #     self.number_of_strands_plus = number_of_strands_plus
    #     self.number_of_sliver_plus = number_of_sliver_plus
    #     self.wires_in_sliver_plus = wires_in_sliver_plus
    #     self.number_of_sliver_extra_plus = number_of_sliver_extra_plus
    #     self.wires_in_sliver_extra_plus = wires_in_sliver_extra_plus
    #     self.number_of_veins_support = number_of_veins_support
    #     self.diameter_support = diameter_support
    #     self.number_of_strands_support = number_of_strands_support
    #     self.number_of_sliver_support = number_of_sliver_support
    #     self.wires_in_sliver_support = wires_in_sliver_support
    #     self.number_of_sliver_extra_support = number_of_sliver_extra_support
    #     self.wires_in_sliver_extra_support = wires_in_sliver_extra_support
    #     self.type_bobbin = type_bobbin
    #     self.volume_bobbin = volume_bobbin
    #     self.time_on_dragger = time_on_dragger
    #     self.time_on_multivare = time_on_multivare
    #     self.time_on_streng = time_on_streng
    #     self.operation_sequence = []
    #     self.task = self.set_task()

    def __init__(self, row):
        self.IDZak = row['IDZak']
        self.account_number = row['Номер счета']
        self.mark = Mark(row['Марка заказа из ЕРП'])
        self.release_date = row['Дата выпуска по заказу']
        self.order_length = row['Количество километров в производство']
        self.number_of_veins = row['Количество жил']
        self.diameter = row['Диаметр проволоки (волочение), мм']
        self.number_of_strands = row['Количество стренг']
        self.number_of_sliver = row['Кол-во зарядных катушек на стренге']
        self.wires_in_sliver = row['Кол-во проволок на одной катушке']
        self.number_of_sliver_extra = row['КоличествоЗарядныхКатушекНаСтренгеДоп']
        self.wires_in_sliver_extra = row['КоличествоПроволокНаОднойКатушкеДоп']
        self.number_of_veins_plus = row['Количество жил плюсовой']
        self.diameter_plus = row['Диаметр проволоки плюсовой']
        self.number_of_strands_plus = row['Количество стренг плюсовой']
        self.number_of_sliver_plus = row['Количество зарядных катушек на стренге плюсовой']
        self.wires_in_sliver_plus = row['Количество проволок на одной катушке плюсовой']
        self.number_of_sliver_extra_plus = row['Количество зарядных катушек на стренге плюсовой доп']
        self.wires_in_sliver_extra_plus = row['КоличествоПроволокНаОднойКатушкеПлюсовойДоп']
        self.number_of_veins_support = row['Количество жил вспомогательный']
        self.diameter_support = row['Диаметр проволоки вспомогательный']
        self.number_of_strands_support = row['Количество стренг вспомогательный']
        self.number_of_sliver_support = row['Количество зарядных катушек на стренге вспомогательный']
        self.wires_in_sliver_support = row['Количество проволок на одной катушке вспомогательный']
        self.number_of_sliver_extra_support = row['Количество зарядных катушек на стренге вспомогательный доп']
        self.wires_in_sliver_extra_support = row['Количество проволок на одной катушке вспомогательный доп']
        self.type_bobbin = row['Вид барабана']
        self.volume_bobbin = row['Километраж масса VSДлина']
        self.time_on_dragger = row['Время на волочилке']
        self.time_on_multivare = row['Время на мультике']
        self.time_on_streng = row['Время на стренге']
        self.operation_sequence = []
        self.task = self.set_task()


    def set_task(self):
        """
        Создаем задания на оборудования, разбивая кабель на несколько составляющих. Если в кабеле есть дополнительные жилы,
        то каждая дополнительная жила в задании будет восприниматься как отдельный заказ с аналогичным номером с добавлением
        +/е/s
        :return: массив, элементы которого задания на различные оборудования по техцепочке
        """
        task = {}

        # Если заказ пойдет на мультик, то у него не должно быть задания на волочилку, т.к. для таких заказов заданием будет являться корзина
        if self.time_on_dragger and not self.time_on_multivare:
            task['WireDrawing']: list = self.set_task_for_dragger()
        if self.time_on_multivare:
            task['Multivare']: list = self.set_task_for_multivare()

        return task

    def set_task_for_dragger(self):
        """
        Заводим Задание на волочилку и добавляем задание в очередь. Тут очередь будет еще не в оптимальном порядке
        :return:
        """
        return Dragger.TaskForDragger(self)

    def set_task_for_multivare(self):
        task = [Multivare.MultivareTask(self, self.diameter, self.number_of_veins, self.number_of_strands,
                                        self.number_of_sliver, self.wires_in_sliver, '')]
        if self.number_of_sliver_extra:
            task.append([Multivare.MultivareTask(self, self.diameter, self.number_of_veins, self.wires_in_sliver_extra,
                                                 self.number_of_sliver_extra,
                                                 self.wires_in_sliver_extra, 'e')])

        if self.mark.cable_parameters.get('Тип') == 'Плюсовой':
            task.append(Multivare.MultivareTask(self, self.diameter_plus, self.number_of_veins_plus,
                                                self.number_of_strands_plus,
                                                self.number_of_sliver_plus,
                                                self.wires_in_sliver_plus, '+'))

            if self.number_of_sliver_extra_plus:
                task.append(
                    [Multivare.MultivareTask(self, self.diameter_plus, self.number_of_veins_plus,
                                             self.number_of_strands_plus,
                                             self.number_of_sliver_extra_plus,
                                             self.wires_in_sliver_extra_plus, 'e+')])

        if self.mark.cable_parameters.get('Тип') == 'Вспомогательный':
            task.append(Multivare.MultivareTask(self, self.diameter, self.number_of_veins_support,
                                                self.number_of_strands_support,
                                                self.number_of_sliver_support,
                                                self.wires_in_sliver_support, 's'))
            if self.number_of_sliver_extra_support:
                task.append(
                    Multivare.MultivareTask(self, self.diameter, self.number_of_veins_support,
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
