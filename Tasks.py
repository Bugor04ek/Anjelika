import weakref
from typing import Any, Union, List


from gosts import Mark
import random
from Equipments import MultivareMachine, WireDrawingMachine, Equipment, MachineMeta

dict_key_group = {}

pi = 3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679821480865132823066470938446095
operation_sequence = ["wiredrawing", "multivare", "rigidframe"]


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

    def __init__(self, row):
        self.time_on_drawing = None
        self.time_on_multivare = None
        self.IDZak = row['IDZakaza']
        self.account_number = row['НомерСчёта']
        self.mark = Mark(row['МаркаЗаказаИзЕРП'])
        self.release_date = row['ДатаВыпускаПоЗаказу']
        self.order_length = row['КоличествоКилометровВПроизводство']
        self.number_of_veins = row['КоличествоЖил']
        self.diameter = row['ДиаметрПроволоки']
        self.voloka = row['Волока']
        self.number_of_strands = row['КоличествоСтренг']
        self.number_of_sliver = row['КоличествоЗарядныхКатушекНаСтренге']
        self.wires_in_sliver = row['КоличествоПроволокНаОднойКатушке']
        self.number_of_sliver_extra = row['КоличествоЗарядныхКатушекНаСтренгеДоп']
        self.wires_in_sliver_extra = row['КоличествоПроволокНаОднойКатушкеДоп']
        self.number_of_veins_plus = row['КоличествоЖилПлюсовой']
        self.diameter_plus = row['ДиаметрПроволокиПлюсовой']
        self.number_of_strands_plus = row['КоличествоСтренгПлюсовой']
        self.number_of_sliver_plus = row['КоличествоЗарядныхКатушекНаСтренгеПлюсовой']
        self.wires_in_sliver_plus = row['КоличествоПроволокНаОднойКатушкеПлюсовой']
        self.number_of_sliver_extra_plus = row['КоличествоЗарядныхКатушекНаСтренгеПлюсовойДоп']
        self.wires_in_sliver_extra_plus = row['КоличествоПроволокНаОднойКатушкеПлюсовойДоп']
        self.number_of_veins_support = row['КоличествоЖилВспомогательный']
        self.diameter_support = row['ДиаметрПроволокиВспомогательный']
        self.number_of_strands_support = row['КоличествоСтренгВспомогательный']
        self.number_of_sliver_support = row['КоличествоЗарядныхКатушекНаСтренгеВспомогательный']
        self.wires_in_sliver_support = row['КоличествоПроволокНаОднойКатушкеВспомогательный']
        self.UUID = row['UUID']
        self.number_of_sliver_extra_support = row['КоличествоЗарядныхКатушекНаСтренгеВспомогательныйДоп']
        self.wires_in_sliver_extra_support = row['КоличествоПроволокНаОднойКатушкеВспомогательныйДоп']
        # self.type_bobbin = row['Вид барабана']
        self.volume_bobbin = row['КилометражМассаVSДлина']
        try:
            self.material = 'al' if self.mark.mark[0] in ['А', 'A'] else 'cu'
        except:
            self.material = 'cu'
        self.operation_sequence = row['ОперацииПоЗаказу']
        self.current_operation_index = 0  # Указатель на текущую операцию
        self.task = self.set_task(row)

    def set_task(self, row):
        """
        Создаем задания на оборудования, разбивая кабель на несколько составляющих. Если в кабеле есть дополнительные жилы,
        то каждая дополнительная жила в задании будет восприниматься как отдельный заказ с аналогичным номером с добавлением
        +/е/s
        :return: массив, элементы которого задания на различные оборудования по техцепочке
        """
        task = {}

        # Если заказ пойдет на мультик, то у него не должно быть задания на волочилку, т.к. для таких заказов заданием будет являться корзина
        if 'Волочение' in self.operation_sequence and not 'Волочение (мультивайер)' in self.operation_sequence:
            self.time_on_drawing = row['ВремяНаВолочение']
            task['wiredrawing']: list = self.set_task_for_dragger()
        if 'Волочение (мультивайер)' in self.operation_sequence:
            self.time_on_multivare = row['ВремяНаВолочениемультивайер']
            task['multivare']: list = self.set_task_for_multivare()

        # self.time_on_streng = row['ВремяНаСкруткастренги']

        # if self.time_on_dragger and not self.time_on_multivare:
        #     task['wiredrawing']: list = self.set_task_for_dragger()
        # if self.time_on_multivare:
        #     task['multivare']: list = self.set_task_for_multivare()

        return task

    def set_task_for_dragger(self):
        """
        Заводим Задание на волочилку и добавляем задание в очередь. Тут очередь будет еще не в оптимальном порядке
        :return:
        """
        task = [WireDrawingTask(self, self.account_number, self.voloka, '', self.time_on_drawing)]
        if self.mark.cable_parameters.get('Тип') == 'Плюсовой':
            task.append(
                WireDrawingTask(self, self.account_number, self.diameter_plus, '+', self.time_on_drawing)
            )

        return task

    def set_task_for_multivare(self):
        task = [MultivareTask(
            self, self.diameter, self.number_of_veins, self.number_of_strands,
            self.number_of_sliver, self.wires_in_sliver, '', self.time_on_multivare
        )]
        if self.number_of_sliver_extra:
            task.append(
                MultivareTask(
                    self, self.diameter, self.number_of_veins, self.wires_in_sliver_extra,
                    self.number_of_sliver_extra,
                    self.wires_in_sliver_extra, 'e', self.time_on_multivare
                )
            )

        if self.mark.cable_parameters.get('Тип') == 'Плюсовой':
            task.append(
                MultivareTask(
                    self, self.diameter_plus, self.number_of_veins_plus,
                    self.number_of_strands_plus,
                    self.number_of_sliver_plus,
                    self.wires_in_sliver_plus, '+', self.time_on_multivare
                )
            )

            if self.number_of_sliver_extra_plus:
                task.append(
                    MultivareTask(
                        self, self.diameter_plus, self.number_of_veins_plus,
                        self.number_of_strands_plus,
                        self.number_of_sliver_extra_plus,
                        self.wires_in_sliver_extra_plus, 'e+', self.time_on_multivare
                    )
                )

        if self.mark.cable_parameters.get('Тип') == 'Вспомогательный':
            task.append(
                MultivareTask(
                    self, self.diameter, self.number_of_veins_support,
                    self.number_of_strands_support,
                    self.number_of_sliver_support,
                    self.wires_in_sliver_support, 's', self.time_on_multivare
                )
            )
            if self.number_of_sliver_extra_support:
                task.append(
                    MultivareTask(
                        self, self.diameter, self.number_of_veins_support,
                        self.number_of_strands_support,
                        self.number_of_sliver_extra_support,
                        self.wires_in_sliver_extra_support, 'es', self.time_on_multivare
                    )
                )

        return task

    def __repr__(self) -> str:
        return "{} | {} | {} | {} | {}".format(
            self.account_number, self.mark.mark, self.mark.cable_parameters, self.release_date, self.order_length
        )


class TaskMeta(type):
    """Метакласс для хранения всех экземпляров заданий на волочилку."""
    _instances = weakref.WeakSet()

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(instance)
        return instance

    @classmethod
    def get_instances_by_type(cls, **kwargs):
        """Возвращает все экземпляры заданий определенного типа оборудования."""
        return [instance for instance in cls._instances for key, val in kwargs.items() if getattr(instance, key) == val]


    @classmethod
    def get_instances_all(cls):
        """Возвращает все экземпляры заданий определенного типа оборудования."""
        return [instance for instance in cls._instances]


class Task(metaclass=TaskMeta):
    """
    Базовый класс для задания на оборудование.
    """

    def __init__(self, order, account_number, time_work, equipment_type=None, part_type=''):
        self.acceptable_equipment: [Equipment] = []
        self.part_type = part_type  # '', '+', 'support'
        self.order = order
        self.account_number = account_number  # Используем номер заказа из Order
        self.equipment_type = equipment_type  # Тип оборудования
        self.equipment = None  # Конкретное оборудование, назначается в генетическом алгоритме
        self.time_work = time_work
        self.current_operation_index = 0  # Индекс текущей операции в цепочке
        self.set_acceptable_equipment()

    def name(self):
        return self.equipment.name

    def next_operation(self):
        """
        Переход к следующей операции в цепочке.
        """
        if self.current_operation_index < len(self.order.operation_sequence) - 1:
            self.current_operation_index += 1
            return self.order.operation_sequence[self.current_operation_index]
        return None  # Завершение операций

    def assign_equipment(self, equipment):
        if self.equipment_type in equipment.equipment_type:
            self.equipment = equipment
            # установить маршрут фильер
            # self.spin_road(self)
            # если старая волочилка, то берем много маршрутов, если другая, то 1

    @staticmethod
    def assign_tasks_to_equipment(tasks: Union[List[Union['MultivareTask', 'WireDrawingTask']], 'Basket']):
        """
        Назначает оборудование для всех заданий, выбирая подходящее.
        """
        if isinstance(tasks, list):
            for task in tasks:
                task.equipment = random.choice(task.acceptable_equipment)
                task.set_spin_road()
        else:
            tasks.equipment = random.choice(tasks.acceptable_equipment)
            tasks.set_spin_road()

    def set_acceptable_equipment(self):
        equipments = MachineMeta.get_all_instances()
        self.acceptable_equipment = [eq for eq in equipments if self.equipment_type in eq.equipment_type and eq.is_suitable(self)]


    @staticmethod
    def form_matrix_multivare(tasks):
        """
        Функция для создания матрицы времени перенастроек мультика
        :param tasks: неупорядоченный список заказов на мультик
        :return: матрица времени перенастроек
        """
        temp_matrix1 = []
        for order1 in tasks:
            temp_matrix2 = []
            for order2 in tasks:
                temp_matrix2.append(order1.calculate_setup_time(order1, order2))
            temp_matrix1.append(temp_matrix2)
        return temp_matrix1

    def __str__(self):
        return f"{self.account_number}{self.part_type} | {self.equipment_type or 'Не назначено'}"


class WireDrawingTask(Task):
    """
    Класс для заказов на волочение. Тут может быть либо обычный заказ, либо корзина состоящая из заказов на мультик.
    """
    # Переменная класса для подсчета индексов
    def __init__(self, order, account_number, diameter, part_type, time_work):
        if issubclass(Order, type(order)):
            self.material = order.material
            # self.time_work = order.time_on_dragger
            self.voloka = diameter
        elif issubclass(Basket, type(order)):
            # self.time_work = WireDrawingMachine.W
            self.voloka = MultivareMachine.d_mult
            self.material = 'cu'
        super().__init__(order, account_number=account_number, equipment_type='wiredrawing', part_type=part_type, time_work=time_work)

        self.comment_setup = ''
        self.time_setup = 0
        self.spin_road = []
        self.time_penalty = 0


    def assign_equipment(self, equipment):
        if self.equipment_type in equipment.equipment_type:
            self.equipment = equipment
            self.set_spin_road()

    def set_spin_road(self):
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        Если находим в справочнике значение фильеры, тогда количество = ключ
        Если не находим, тогда ищем после какой фильеры нужно поставить еще одну количество = ключ + 1
        :return: количество фильер
        """
        # маршрут записанный из ключевых волок, последняя волока -- минимально возможный диаметр
        roads = self.equipment.spinners_road
        if self.equipment.equipment_name != 'old':
            # на новой и алюминиевой волочилке будет один маршрут
            for i, voloka in enumerate(roads):
                if self.voloka >= voloka:
                    # меняем волоку на большую и меняем маршрут
                    self.spin_road = self.equipment.spinners_road[:i]
                    while i != len(roads) - 1:
                        self.spin_road.append(0)
                        i += 1
                    self.spin_road.append(self.voloka)
                    break
        else:
            # на старой волочилке может быть много маршрутов
            for road in roads:
                if abs(self.voloka - road[0][-1]) <= WireDrawingMachine.diameter_range: #Находится ли текущая волока в допустимом диапазоне
                    self.spin_road = road
                    break

    @staticmethod
    def calculate_setup_time(current_task: "WireDrawingTask", previous_task: "WireDrawingTask"):
        """Расчет времени перенастройки между заданиями."""

        setup_time = 0
        current_task.comment_setup = ''

        if current_task.equipment.equipment_name != 'old':  # Алюминиевая и Новая волочилка
            # проходим по маршрутам и ищем, где начинается расхождение, чтобы после этой фильеры обрезать проволочку и снять все фильеры
            for i in range(min(len(current_task.spin_road), len(previous_task.spin_road))):
                if current_task.spin_road[i] != previous_task.spin_road[i]:
                    # разница уникальных волок в маршруте
                    diff_spin = i
                    break
            else:
                # если одинаковые волоки
                return setup_time

            # снимаем фильеры с предыдущего задания
            spin_in_with_0 = len(previous_task.spin_road) - diff_spin
            spin_in_without_0 = [e for e in previous_task.spin_road[-spin_in_with_0:] if e != 0]
            spin_out = len(previous_task.spin_road) - diff_spin  # это всегда будет 1 волока
            current_task.comment_setup = 'снять {} волок ({});'.format(len(spin_in_without_0), spin_in_without_0)
            setup_time += len(spin_in_without_0) * WireDrawingMachine.CHANGE_WIRE + len(spin_in_without_0) * WireDrawingMachine.REMOVED_SPIN + WireDrawingMachine.STRETCHING_WIRE

            # вставляем волоки с текущего задания
            spin_in_with_0 = len(current_task.spin_road) - diff_spin
            spin_in_without_0 = sum([1 for e in current_task.spin_road[-spin_in_with_0:] if e != 0])
            spin_in_values = [e for e in current_task.spin_road[-spin_in_with_0:] if e != 0] # Список значений фильер, которые нужно поставить, без нулей
            current_task.comment_setup += 'вставить {} волок ({});'.format(spin_in_without_0, spin_in_values)
            setup_time += spin_in_without_0 * WireDrawingMachine.CHANGE_WIRE + spin_in_without_0 * WireDrawingMachine.INSERT_SPIN + WireDrawingMachine.STRETCHING_WIRE

            setup_time += WireDrawingMachine.CHANGE_BOBBIN

        else:  # Старая волочилка
            best_road = {}


            for road1 in current_task.spin_road:
                spin_road2 = previous_task.spin_road

                for road2 in spin_road2:
                    for i in range(min(len(road1), len(road2))):
                        if road1[i] != road2[i]:
                            # разница уникальных волок в маршруте
                            diff_spin = i
                            break
                    else:
                        best_road[tuple(road1),tuple(road2)] = 0
                        continue

                    # снимаем фильеры с предыдущего задания
                    if len(road1) != len(road2):

                        spin_out = len(road2) - diff_spin
                        current_task.comment_setup = 'снять {} волок ({});'.format(spin_out, road2[-spin_out:])
                        setup_time += spin_out * WireDrawingMachine.CHANGE_WIRE + spin_out * WireDrawingMachine.REMOVED_SPIN + WireDrawingMachine.STRETCHING_WIRE

                        # вставляем волоки с текущего задания
                        spin_in = abs(len(road1) - len(road2))
                        current_task.comment_setup += 'вставить {} волок ({});'.format(spin_in, road1[-(len(road1) - diff_spin):])
                        setup_time += spin_in * WireDrawingMachine.CHANGE_WIRE + len(road1) * WireDrawingMachine.INSERT_SPIN + WireDrawingMachine.STRETCHING_WIRE

                        best_road[tuple(road1),tuple(road2)] = setup_time
                    else:
                        spin_out = len(road2) - diff_spin
                        current_task.comment_setup += 'снять {} волок ({});'.format(spin_out, road2[-spin_out:])
                        setup_time += spin_out * WireDrawingMachine.CHANGE_WIRE + spin_out * WireDrawingMachine.REMOVED_SPIN + WireDrawingMachine.STRETCHING_WIRE

                        # вставляем волоки с текущего задания
                        spin_in = len(road1) - diff_spin
                        current_task.comment_setup += 'вставить {} волок ({});'.format(spin_in, road1[-spin_in:])
                        setup_time += spin_in * WireDrawingMachine.CHANGE_WIRE + spin_in * WireDrawingMachine.INSERT_SPIN + WireDrawingMachine.STRETCHING_WIRE

                        best_road[tuple(road1),tuple(road2)] = setup_time

                    setup_time = 0
            else:

                current_task.spin_road = [list(sorted(best_road.items(), key=lambda x: x[1])[0][0][0])]
                setup_time = sorted(best_road.items(), key=lambda x: x[1])[0][1]

                if len(previous_task.spin_road) > 1:
                    previous_task.spin_road = [list(sorted(best_road.items(), key=lambda x: x[1])[0][0][1])]

        current_task.time_setup = setup_time

        return setup_time

    @staticmethod
    def calculate_setup_time_all(tasks: ["WireDrawingTask"]):
        for i in range(1, len(tasks)):
            WireDrawingTask.calculate_setup_time(tasks[i], tasks[i - 1])

    @staticmethod
    def create_basket_refill_task(basket):
        """Создаёт задание на пополнение корзин на волочилке для конкретного оборудования."""
        refill_task = WireDrawingTask(order=basket, account_number=None, diameter=None, part_type=None, time_work=WireDrawingMachine.W)
        WireDrawingTask.assign_tasks_to_equipment(refill_task)
        print(f"Создано задание на пополнение {8} корзин для {refill_task.equipment.equipment_name}.")

    def __repr__(self):
        if issubclass(Order, type(self.order)):
            return '{} {} -- {} \n'.format(self.account_number, self.order.mark.mark, self.equipment)
        elif issubclass(Basket, type(self.order)):
            return '{}\n'.format(self.order.__repr__())


class MultivareTask(Task):
    """
    Задание на мультик хранит в переменной класса хранит все заказы в массиве, их можно будет найти по IDZak
    """

    def __init__(self, order, diameter, number_of_veins, number_of_strands, number_of_sliver, wires_in_sliver, type, time_work):
        super().__init__(order, account_number=order.account_number, equipment_type='multivare', part_type=type, time_work=time_work)
        # self.volume_bobbin = order.volume_bobbin
        # 350 - Ограничение по массе барабана для гибкой жилы на 630 барабан
        # 8.89 - Плотность меди
        self.velocity = 0
        self.volume_bobbin = 350 / (
                pi * 0.25 * 8.89 * order.diameter ** 2 * max(order.wires_in_sliver, order.wires_in_sliver_extra))
        self.IDZak = order.IDZak
        self.account_number = order.account_number + type
        self.comment_setup = ''
        self.diameter = diameter
        self.number_of_sliver = number_of_sliver
        self.wires_in_sliver = wires_in_sliver
        self.number_of_veins = number_of_veins
        self.number_of_strands = number_of_strands
        self.group = ()
        self.num_group = 0
        self.spin_road = []
        self.total_weight_delays = 0
        self.length_piece = 0
        self.length_strands = 0
        self.full_bobbin = ()
        self.time_on_multivare = order.time_on_multivare
        self.time_on_mult_1_basket = 0
        self.__time_setup = 0
        self.num_basket = 0
        # self.counting_spinners()
        # self.set_group()
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

        self.spin = MultivareMachine.dictionary_spinners[min(MultivareMachine.dictionary_spinners, key=lambda x: abs(self.diameter - x))]

    def calculating_length(self):
        # суммарная длина проволочек

        self.total_weight_delays = ((self.number_of_sliver * self.wires_in_sliver) * self.number_of_strands *
                                    self.number_of_veins * self.order.order_length) * pi * 8.89 * (
                                           self.diameter ** 2) * 0.25
        self.length_piece = round(self.total_weight_delays * (self.diameter ** 2 / MultivareMachine.d_mult ** 2), 3)

        # 0 - сколько корзин по 8 штук нужно, если заказ очень большой и требуется много корзин
        # 1 - сколько корзин еще заполнится (набирается число до 8)
        self.num_basket1 = (
             int(self.total_weight_delays * 1 / (pi * 0.25 * 8.89 * MultivareMachine.d_mult ** 2) / MultivareMachine.KM_IN_1_BASKET // 8),
             self.total_weight_delays * 1 / (pi * 0.25 * 8.89 * MultivareMachine.d_mult ** 2) / MultivareMachine.KM_IN_1_BASKET % 8
        )
        self.num_basket = self.total_weight_delays * 1 / (pi * 0.25 * 8.89 * MultivareMachine.d_mult ** 2) / MultivareMachine.KM_IN_1_BASKET
        self.velocity = self.num_basket / self.time_on_multivare  #(self.num_basket[0] + self.num_basket[1])

        # Пока у нас не назначено оборудование просто создаем класс корзины и считаем длину.
        # Не записываем ни оборудование, ни список заказов
        # basket = None
        # if self.equipment is None:
        #     basket = Basket()
        # self.update_basket_status()

        # длина заказа в расчете на одну прядь (весь заказ это length_strands *
        # (number_of_sliver + number_of_sliver_extra))
        self.length_strands = round((self.order.order_length * self.number_of_veins * self.number_of_strands), 2)

        # подсчет барабанов
        self.calculating_bobbin()

    def update_basket_status(self, current_basket_count, equipment):
        """Обновляет количество оставшихся корзин для мультика."""
        if current_basket_count < self.num_basket:
            # Подсчитываем, сколько еще корзин необходимо заполнить
            needed_baskets = 8
            WireDrawingTask.create_basket_refill_task(needed_baskets, equipment)

    def calculating_bobbin(self):
        number_full_bobbin = self.length_strands // self.volume_bobbin  # количество полных катушек в расчете на 1 прядь
        volume_half_bobbin = round(self.length_strands % self.volume_bobbin, 2)  # меди на неполной катушки на 1 прядь

        self.full_bobbin = int(number_full_bobbin), volume_half_bobbin, int(int(number_full_bobbin) > 0)

    def set_spin_road(self):
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        Если находим в справочнике значение фильеры, тогда количество = ключ
        Если не находим, тогда ищем после какой фильеры нужно поставить еще одну количество = ключ + 1
        :return: количество фильер
        """
        # маршрут записанный из ключевых волок, последняя волока -- минимально возможный диаметр
        roads = self.equipment.spinners_road

        # на новой и алюминиевой волочилке будет один маршрут

        self.spin_road = [min(roads, key=lambda x: abs(self.diameter - x[-1]))]

    @staticmethod
    def calculate_setup_time(current_task: "MultivareTask", previous_task: "MultivareTask"):
        """
        Функция для расчета времени перенастройки между заказами мультика.
        Считается время перенастройки и смены катушки между заказами
        Не учитывается добавление катушки, если она заполнена
        ??? После определения оптимального варианта будет пересчет через чеклист мультика
        :param current_task:
        :param previous_task:current_task
        :return:
        """

        total_setup_time = 0
        current_task.comment_setup = ''

        if previous_task is not None:
            """
                1 ПРОВЕРКА -- Разность диаметров
            """

            setup_time = 0
            diff_spin = 0

            best_road = {}
            for road1 in current_task.spin_road:
                spin_road2 = previous_task.spin_road

                for road2 in spin_road2:
                    for i in range(min(len(road1), len(road2))):
                        if road1[i] != road2[i]:
                            # разница уникальных волок в маршруте
                            diff_spin = i
                            break
                    else:
                        best_road[tuple(road1), tuple(road2)] = 0
                        continue

                    # снимаем фильеры с предыдущего задания
                    if len(road1) != len(road2):

                        spin_out = len(road2) - diff_spin
                        current_task.comment_setup = 'снять {} волок ({});'.format(spin_out, road2[-spin_out:])
                        setup_time += spin_out * MultivareMachine.CHANGE_WIRE + spin_out * MultivareMachine.REMOVED_SPIN + MultivareMachine.STRETCHING_WIRE

                        # вставляем волоки с текущего задания
                        spin_in = abs(len(road1) - len(road2))
                        current_task.comment_setup += 'вставить {} волок ({});'.format(spin_in, road1[-(
                                    len(road1) - diff_spin):])
                        setup_time += spin_in * MultivareMachine.CHANGE_WIRE + len(
                            road1) * MultivareMachine.INSERT_SPIN + MultivareMachine.STRETCHING_WIRE

                        best_road[tuple(road1), tuple(road2)] = setup_time
                    else:
                        spin_out = len(road2) - diff_spin
                        current_task.comment_setup += 'снять {} волок ({});'.format(spin_out, road2[-spin_out:])
                        setup_time += spin_out * MultivareMachine.CHANGE_WIRE + spin_out * MultivareMachine.REMOVED_SPIN + MultivareMachine.STRETCHING_WIRE

                        # вставляем волоки с текущего задания
                        spin_in = len(road1) - diff_spin
                        non_zero_dies = [value for value in road1[-spin_in:] if value != 0] # Не нулевые фильеры
                        current_task.comment_setup += 'вставить {} волок ({});'.format(len(non_zero_dies), non_zero_dies)
                        setup_time += spin_in * MultivareMachine.CHANGE_WIRE + spin_in * MultivareMachine.INSERT_SPIN + MultivareMachine.STRETCHING_WIRE

                        best_road[tuple(road1), tuple(road2)] = setup_time

                    diff_spin = 0
                    current_task.spin_road = [list(sorted(best_road.items(), key=lambda x: x[1])[0][0][0])]
                    setup_time = sorted(best_road.items(), key=lambda x: x[1])[0][1]
                    current_task.time_setup = setup_time
            else:

                current_task.spin_road = [list(sorted(best_road.items(), key=lambda x: x[1])[0][0][0])]
                setup_time = sorted(best_road.items(), key=lambda x: x[1])[0][1]

                # if len(previous_task.spin_road) > 1:
                #     previous_task.spin_road = [list(sorted(best_road.items(), key=lambda x: x[1])[0][0][1])]

        current_task.time_setup = setup_time

        return setup_time

    @staticmethod
    def calculate_setup_time_all(tasks: ["WireDrawingTask"]):
        for i in range(1, len(tasks)):
            MultivareTask.calculate_setup_time(tasks[i], tasks[i - 1])

    @property
    def time_setup(self):
        return self.__time_setup

    @time_setup.setter
    def time_setup(self, value):
        self.__time_setup = value

    # def __str__(self) -> str:
    #     # return "{} | {} | {} | {} | {} | {} | {} | {} | {}".format(
    #     #     self.id, self.account_number, self.num_group, self.order.release_date, self.length_strands, self.group,
    #     #     self.full_bobbin, self.time_on_mult, self.order.time_on_streng
    #     # )
    #
    #     return "{} | {} | {} | {}".format(
    #         self.account_number, self.order.release_date, self.group,
    #         self.full_bobbin, self.time_on_mult_1_basket
    #     )

    def __repr__(self):
        return '{} {} -- {} \n'.format(self.account_number, self.order.mark.mark, self.equipment)

    def match(self, **kwargs):
        return all(getattr(self, key) == val for (key, val) in kwargs.items())


class BasketMeta(type):
    """
    Метакласс для отслеживания всех экземпляров корзин.
    """
    _instances = weakref.WeakSet()

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(instance)
        return instance

    @classmethod
    def get_instances_by_type(cls, **kwargs):
        """Возвращает все экземпляры заданий определенного типа оборудования."""
        return [instance for instance in cls._instances for key, val in kwargs.items() if getattr(instance, key) == val]


class Basket:
    """
    Корзина для подачи на мультик. Класс создается когда заказы с мультика израсходуют суммарно 8 корзин.
    Класс передается в очередь на волочилку.
    """

    def __init__(self, order, sum_basket=0):
        """
        Создание корзины. Когда будет несколько заказов в корзинах, тогда используются значения параметров по умолчанию.
        Если один заказ тратит 8 корзин, тогда используются переданные параметры
        :param order: None, если заказа нет, значит создаем корзину с остатками с предыдущей корзины. Не None, если 1 заказ
        :param sum_basket: 0, если много заказов. 8, если 1 заказ
        """

        if order is not None:
            # Если заказ указан при инициализации, значит что это остаток с другой корзины, значит время перенастройки было уже учтенео
            self.orders: [MultivareTask] = [order]
            self.time_on_multivare = sum_basket * order.velocity
        else:
            self.orders: [MultivareTask] = []
            self.time_on_multivare = 0

        self.material = 'cu'
        self.voloka = MultivareMachine.d_mult
        self.diameter = MultivareMachine.d_mult
        self.len_basket = MultivareMachine.KM_IN_1_BASKET * 8
        self.sum_basket = sum_basket
        self.equipment_type = 'wiredrawing'
        self.time_work = WireDrawingMachine.W
        self.acceptable_equipment = []
        self.set_acceptable_equipment()
        WireDrawingTask.assign_tasks_to_equipment(self)

    def set_acceptable_equipment(self):
        equipments = MachineMeta.get_all_instances()
        self.acceptable_equipment = [eq for eq in equipments if self.equipment_type in eq.equipment_type and eq.is_suitable(self)]

    def append(self, order: MultivareTask, num_basket: float, use_time_setup=True):
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
        # if num_basket is None:
        # Тут берем траты корзины из заказа
        self.time_on_multivare += num_basket / order.velocity + order.time_setup
        self.sum_basket += num_basket
        # else:
        #     # Тут берем траты корзины из параметра
        #     self.time_work += order.time_on_mult_1_basket * num_basket + (order.time_setup if use_time_setup else 0)
        #     self.sum_basket += num_basket

    def append_setup_time(self):
        """
        После того как знаем задание на мультик добавляем ко времени 'self.time_on_multivare' время перестановок из массива внутри корзины
        :return:
        """
        for order in self.order:
            self.time_on_multivare += order.time_on_multivare

    def set_spin_road(self):
        """
        Находим в словаре фильер ближайшие значения к диаметру.
        Если находим в справочнике значение фильеры, тогда количество = ключ
        Если не находим, тогда ищем после какой фильеры нужно поставить еще одну количество = ключ + 1
        :return: количество фильер
        """
        # маршрут записанный из ключевых волок, последняя волока -- минимально возможный диаметр
        roads = self.equipment.spinners_road
        if self.equipment.equipment_name != 'old':
            # на новой и алюминиевой волочилке будет один маршрут
            for i, voloka in enumerate(roads):
                if self.voloka >= voloka:
                    # меняем волоку на большую и меняем маршрут
                    self.spin_road = self.equipment.spinners_road[:i]
                    while i != len(roads) - 1:
                        self.spin_road.append(0)
                        i += 1
                    self.spin_road.append(self.voloka)
                    break
        else:
            # на старой волочилке может быть много маршрутов
            for road in roads:
                if abs(self.voloka - road[0][-1]) <= WireDrawingMachine.diameter_range: #Находится ли текущая волока в допустимом диапазоне
                    self.spin_road = road
                    break

    def __repr__(self):
        return 'Корзина (Время работы заказов = {}ч. {}мин.; Длина {}): {} \n'.format(
            str(self.time_work // 60),
            str(round(self.time_work % 60, 2)),
            self.sum_basket,
            self.orders.__repr__()
        )
