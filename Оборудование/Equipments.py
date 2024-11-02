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


class TaskMeta(type):
    """Метакласс для хранения всех экземпляров заданий на волочилку."""
    _instances = weakref.WeakSet()

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(instance)
        return instance

    @classmethod
    def get_instances_by_type(cls, equipment_type):
        """Возвращает все экземпляры заданий определенного типа оборудования."""
        return [instance for instance in cls._instances if instance.equipment_type == equipment_type]


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
        }
    }

    def __init__(self, name, machine_type, supported_materials):
        self.name = name
        self.machine_type = machine_type.lower()
        self.supported_materials = supported_materials
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

    @classmethod
    def get_all_instances(cls, names=None):
        if names is None:
            return list(cls._instances)
        return [instance for instance in cls._instances if instance.name in names]
