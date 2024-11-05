import os
import pandas as pd
from pandas import ExcelWriter


# class QueueMultivare:
#     """
#     Оптимальная очередь на мультике. С методами поиска любого заказа по заданным параметрам
#     """
#
#     rest_basket: float = 0.0
#     rest_orders: [MultivareTask] = []
#
#     def __init__(self):
#         self.__queue: [MultivareTask] = []
#
#     @property
#     def queue(self):
#         return self.__queue
#
#     @queue.setter
#     def queue(self, orders):
#         self.__queue = orders
#
#     def __add__(self, other):
#         self.__queue.append(other)
#
#     def find_order(self, **kwargs):
#         return next(self.__iter_order(**kwargs))
#
#     def all_orders(self, **kwargs):
#         return list(self.__iter_order(**kwargs))
#
#     def __iter_order(self, **kwargs):
#         return (order for order in self.__queue if order.match(**kwargs))
#
#     @staticmethod
#     def calculate_setup_time_multivare(previous_order, order):
#         """
#         Функция для расчета времени перенастройки между заказами мультика.
#         Считается время перенастройки и смены катушки между заказами
#         Не учитывается добавление катушки, если она заполнена
#         ??? После определения оптимального варианта будет пересчет через чеклист мультика
#         :param previous_order:
#         :param order:
#         :return:
#         """
#
#         total_setup_time = 0
#
#         if previous_order is not None:
#
#             change = False
#
#             """
#                 1 ПРОВЕРКА -- Разность диаметров
#             """
#
#             # меньше диаметр - больше фильер
#             if previous_order.spin > order.spin:
#                 removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
#                 total_setup_time += removed_spin * MultivareMachine.REMOVED_SPIN  # Время на снятие фильер
#                 total_setup_time += MultivareMachine.INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер
#                 change = True
#             # больше диаметр - меньше фильер
#             elif previous_order.spin < order.spin:
#                 removed_spin = 1  # снимаем последнюю
#                 total_setup_time += removed_spin * MultivareMachine.REMOVED_SPIN  # время на снятие фильер
#                 total_setup_time += MultivareMachine.INSERT_SPIN * (
#                         order.spin - (
#                         previous_order.spin - 1)) * order.wires_in_sliver  # время на установку фильер +1, потому 1 уже снята tt
#                 change = True
#
#             """
#                 2 ПРОВЕРКА -- Разность проволочек
#             """
#
#             dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)
#
#             if previous_order.wires_in_sliver < order.wires_in_sliver:
#                 # Надо протянуть новые проволочки через все фильеры на новом заказе
#                 total_setup_time += dif_wire * order.spin * MultivareMachine.CHANGE_WIRE + MultivareMachine.STRETCHING_WIRE
#                 change = True
#             elif previous_order.wires_in_sliver > order.wires_in_sliver:
#                 # Надо снять проволочки со всех фильер previous_order
#                 total_setup_time += dif_wire * previous_order.spin * MultivareMachine.CHANGE_WIRE
#                 change = True
#
#             # после каждого заказа будет смена заказа
#             # if change:
#             #     # Если было любое изменение, то надо сменить катушку
#             #     total_setup_time += CHANGE_BOBBIN  # Время на смену катушки
#
#         return total_setup_time
#
#     @staticmethod
#     def form_matrix_multivare(orders):
#         """
#         Функция для создания матрицы времени перенастроек мультика
#         :param orders: неупорядоченный список заказов на мультик
#         :return: матрица времени перенастроек
#         """
#         temp_matrix1 = []
#         for order1 in orders:
#             temp_matrix2 = []
#             for order2 in orders:
#                 temp_matrix2.append(QueueMultivare.calculate_setup_time_multivare(order1, order2))
#             temp_matrix1.append(temp_matrix2)
#         return temp_matrix1
#
#     @staticmethod
#     def get_total_time(time_on_multivare, indices):
#         """
#         Считается время перенастроек между заказов для текущей очереди
#         :param time_on_multivare: время перенастроек для каждого заказа с каждым
#         :param indices: текущий индивид (очередь).
#         :return: Всё время перенастроек для текущей очереди
#         """
#
#         time = 0
#
#         # время между каждой парой заказов
#         for i in range(len(indices) - 1):
#             time += time_on_multivare[indices[i]][indices[i + 1]]
#
#         return time,
#
#     def setting_time_setup(self):
#         """
#         Определяем время настройки заказов на мультике.
#         :return:
#         """
#
#         for i in range(len(self.__queue)):
#
#             # пропускаем первый индекс, т.к у него нет время на перенастройку
#             if i == 0:
#                 continue
#
#             self.__queue[i].time_setup = QueueMultivare.calculate_setup_time_multivare(self.__queue[i - 1],
#                                                                                        self.__queue[i])
#
#     def calculating_basket(self):
#         """
#         Для оптимально расставленных заказов на мультике считаются корзины. Корзина набивается заказами, которые сами по себе не формируют полноценные 8,
#         если такие заказы есть, то заказ должен занимать нужное количество корзин в одиночку, а остаток делить с остальными заказами
#         :return:
#         """
#
#         sum_basket: int = 0
#         temp_basket: Basket = Basket()
#         for order in self.__queue:
#
#             # Если со следующим заказом получается меньше 8 корзин, но он занимает сам по себе больше 8 корзин
#             if order.num_basket[0] > 0 and (sum_basket + order.num_basket[1]) <= 8:
#                 rest_basket = 8 - sum_basket  # сколько нужно до 8 корзин
#                 temp_num_basket = (order.num_basket[0] - 1, order.num_basket[1] + (8 - rest_basket))
#                 # распределяем полные корзины -> (2 (полные корзины), 5.47 (неполные корзины) -> (1, 5.47) -> (1, 13.47 + (8 - rest_basket))
#                 # Добавляем такой заказ последним и начинаем новые корзины, потому что после него пойдут корзины только для этого заказа
#                 sum_basket += rest_basket
#                 temp_basket.append(order, rest_basket)
#                 Dragger.queue_dragger_new_dragger.append(Dragger.WireDrawingTask(temp_basket))
#
#                 for _ in range(temp_num_basket[0]):
#                     Dragger.queue_dragger_new_dragger.append(Dragger.WireDrawingTask(Basket([order], 8)))
#
#                 sum_basket = 0
#                 temp_basket: Basket = Basket()
#                 sum_basket += temp_num_basket[1]
#                 temp_basket.append(order, num_basket=temp_num_basket[1], use_time_setup=False)
#
#             # Если со следующим заказом получается больше 8 корзин
#             elif (sum_basket + order.num_basket[1]) > 8:
#                 # Прибавляем так, чтобы стало 8 и добавляем время изготовления этой части корзины
#                 rest_basket = 8 - sum_basket  # сколько нужно до 8 корзин
#                 temp_basket.append(order, rest_basket)
#                 Dragger.queue_dragger_new_dragger.append(Dragger.WireDrawingTask(temp_basket))
#
#                 # Если заказ на больше 8 корзин, то между корзин будут корзины с 1 этим заказом
#                 for _ in range(order.num_basket[0]):
#                     Dragger.queue_dragger_new_dragger.append(Dragger.WireDrawingTask(Basket([order], 8)))
#
#                 # начинаем новую корзину и добавляем в нее остаток текущего заказа
#                 temp_basket: Basket = Basket()
#                 sum_basket = order.num_basket[1] - rest_basket  # сколько корзин нужно
#                 temp_basket.append(order, sum_basket, False)
#                 # Переходим к следующему заказу, т.к. этот полностью исчерпан
#             else:
#                 sum_basket += order.num_basket[1]
#                 temp_basket.append(order)
#         else:
#             if len(temp_basket.orders) > 0:
#                 # Dragger.queue_dragger.append(Dragger.TaskForDragger(temp_basket))
#                 QueueMultivare.rest_basket += sum_basket
#                 QueueMultivare.rest_orders = temp_basket


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


# queue_multivare = QueueMultivare()
# check_list_multik = CheckListMultivare()


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
