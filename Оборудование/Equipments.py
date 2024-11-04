import weakref

operation_sequence = ["WireDrawing", "Multiwire", "RigidFrame"]


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
