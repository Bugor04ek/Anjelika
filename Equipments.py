import weakref
import Tasks


class MachineMeta(type):
    """
    Метакласс для отслеживания всех созданных экземпляров.
    """
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._instances = weakref.WeakSet()

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(instance)
        return instance


class WireDrawingMachine(metaclass=MachineMeta):
    REMOVED_SPIN = 1  # время снятия фильер
    INSERT_SPIN = 5  # время вставки фильер
    CHANGE_BOBBIN = 5  # смена катушки
    CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
    STRETCHING_WIRE = 5  # протягивание проволочки в отжиге
    W = 12 * 60  # время изготовления 8 корзин

    spinner_dicts = {
        'new': {
            7: 1, 5.75: 2, 4.8: 3, 4.03: 4, 3.43: 5, 2.95: 6,
            2.56: 7, 2.25: 8, 1.99: 9, 1.78: 10, 1.58: 11,
            1.41: 12, 1.35: 13, 1.25: 14
        },
        'old': {
            7: 1, 6.80: 2, 5.15: 3, 4.50: 4, 3.90: 5, 3.45: 6,
            2.95: 7, 2.60: 8, 2.00: 9, 1.65: 10, 1.40: 11, 1.15: 12
        },
        'al': {
            9: 1, 8.15: 2, 7.05: 3, 6.15: 4, 5.39: 5, 4.72: 6,
            4.14: 7, 3.64: 8, 3.20: 9, 2.80: 10, 2.48: 11,
            2.20: 12, 1.93: 13, 1.70: 14
        }
    }

    def __init__(self, name, machine_type, supported_materials):
        self.name = name
        self.machine_type = machine_type.lower()
        self.supported_materials = supported_materials
        self.spinner_dict = WireDrawingMachine.get_spinner_dict(self.machine_type)
        self.spinner_dict = getattr(self, f"{self.machine_type}_spinner_dict")
        self.min_diameter = min(self.spinner_dict.keys())
        self.max_diameter = max(self.spinner_dict.keys())

    new_spinner_dict = {
        7: 1, 5.75: 2, 4.8: 3, 4.03: 4, 3.43: 5, 2.95: 6,
        2.56: 7, 2.25: 8, 1.99: 9, 1.78: 10, 1.58: 11,
        1.41: 12, 1.35: 13, 1.25: 14
    }

    old_spinner_dict = {
        7: 1, 6.80: 2, 5.15: 3, 4.50: 4, 3.90: 5, 3.45: 6,
        2.95: 7, 2.60: 8, 2.00: 9, 1.65: 10, 1.40: 11, 1.15: 12
    }

    al_spinner_dict = {
        9: 1, 8.15: 2, 7.05: 3, 6.15: 4, 5.39: 5, 4.72: 6,
        4.14: 7, 3.64: 8, 3.20: 9, 2.80: 10, 2.48: 11,
        2.20: 12, 1.93: 13, 1.70: 14
    }

    @classmethod
    def get_spinner_dict(cls, machine_type):
        return cls.spinner_dicts.get(machine_type, {})

    def is_suitable(self, material, diameter):
        return material in self.supported_materials and self.min_diameter <= diameter <= self.max_diameter

    def calculate_setup_time(self, current_task, previous_task):
        """Расчет времени перенастройки между заданиями."""
        if not previous_task:
            return 0

        setup_time = 0
        change = False

        if previous_task.spinner_count > current_task.spinner_count:
            removed_spin = previous_task.spinner_count - current_task.spinner_count + 1
            setup_time += removed_spin * self.REMOVED_SPIN
            setup_time += self.INSERT_SPIN
            change = True
        elif previous_task.spinner_count < current_task.spinner_count:
            removed_spin = 1
            setup_time += removed_spin * self.REMOVED_SPIN
            setup_time += self.INSERT_SPIN * (current_task.spinner_count - (previous_task.spinner_count - 1))
            change = True

        if change:
            setup_time += self.CHANGE_BOBBIN

        return setup_time

    @classmethod
    def get_all_instances(cls, names=None):
        if names is None:
            return list(cls._instances)
        return [instance for instance in cls._instances if instance.name in names]


class MultivareMachine(metaclass=MachineMeta):
    REMOVED_SPIN = 1  # время снятия фильер
    INSERT_SPIN = 5  # время вставки фильер (это время надо умножить на количество проволочек в пряди)
    CHANGE_BASKET = 20  # смена корзины на мультике
    CHANGE_BOBBIN = 5  # смена катушки на мультике
    CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
    STRETCHING_WIRE = 5  # протягивание пучка проволочек после всех фильер
    KM_IN_1_BASKET = 35  # КМ в 1 корзине
    KM_IN_8_BASKET = KM_IN_1_BASKET * 8  # КМ в 8 корзинах
    KM_IN_16_BASKET = KM_IN_1_BASKET * 16  # КМ в 8 корзинах

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
        # self.total_baskets = MultivareMachine.KM_IN_16_BASKET  # всего корзин
        # self.remaining_basket_length = MultivareMachine.KM_IN_8_BASKET  # начальный запас длины для 8 корзин

    def is_suitable(self, material, quantity):
        return material in self.supported_materials and quantity <= self.capacity

    @classmethod
    def get_all_instances(cls, names=None):
        if names is None:
            return list(cls._instances)
        return [instance for instance in cls._instances if instance.name in names]


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
        self.orders: ['Tasks.MultivareTask'] = orders
        self.diameter = MultivareMachine.d_mult
        self.len_basket = MultivareMachine.KM_IN_1_BASKET * 8
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

    def append(self, order: 'Tasks.MultivareTask', num_basket=None, use_time_setup=True):
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
