import abc
import json

import weakref

# Equipments.py
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from Tasks import MultivareTask, WireDrawingTask, Order, Basket, TaskMeta


class MachineMeta(type):
    """
    Метакласс для отслеживания всех созданных экземпляров.
    """
    _instances = weakref.WeakSet()

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(instance)
        return instance

    @classmethod
    def get_all_instances(cls):
        return list(cls._instances)


class Equipment(metaclass=MachineMeta):

    def __init__(self, name: '', machine_type: [''], receiver_type_bobbin, working_hours):
        self.equipment_name = name
        self.equipment_type = machine_type
        self.working_hours = working_hours

    # def get_queue(self):
    #     """Получаем очередь из `TaskMeta`, но только для этого оборудования."""
    #     return TaskMeta.get_ready_tasks(self.equipment_types)

    @classmethod
    def get_all_instances(cls, type=None):
        if type is None:
            return list(cls._instances)
        return [instance for instance in cls._instances if type in instance.equipment_type]

    @classmethod
    def get_instances_by_type(cls, **kwargs):
        """Возвращает все экземпляры заданий определенного типа оборудования."""
        return [instance for instance in cls._instances for key, val in kwargs.items() if getattr(instance, key) == val]


class WireDrawingMachine(Equipment):
    REMOVED_SPIN = 1  # время снятия фильер
    INSERT_SPIN = 5  # время вставки фильер
    CHANGE_BOBBIN = 5  # смена катушки
    CHANGE_WIRE = 1.5  # снятие/натягивание проволочки на 1 фильере
    STRETCHING_WIRE = 5  # протягивание проволочки в отжиге
    W = 12 * 60  # время изготовления 8 корзин
    diameter_range = 0.02  # Допустимое отклонение от точного диаметра

    def __init__(
        self, name: str, machine_type: [''], supported_materials: [''], basket: bool, spinners_road: [],
        min_diameter, max_diameter, receiver_type_bobbin, working_hours
        ):
        super().__init__(name, machine_type, receiver_type_bobbin, working_hours)
        self.supported_materials = supported_materials
        self.basket = basket
        self.spinners_road = spinners_road
        # self.facts_diameter = facts_diameter
        self.min_diameter = min_diameter
        self.max_diameter = max_diameter

    def is_suitable(self, task: "WireDrawingTask"):
        return (task.material in self.supported_materials and
                self.min_diameter <= task.voloka <= self.max_diameter and
                (not (task.__class__.__name__ == 'Basket') or (
                            task.__class__.__name__ == 'Basket' and self.basket)))

    # @classmethod
    # def get_all_instances(cls, names=None):
    #     if names is None:
    #         return list(cls._instances)
    #     return [instance for instance in cls._instances if instance.name in names]

    def __repr__(self):
        return f"WireDrawingMachine(name={self.equipment_name}, machine_type={self.equipment_type})"


class MultivareMachine(Equipment):
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

    def __init__(self, name, machine_type, supported_materials, total_baskets, remaining_basket_length, spinners_road,
                 receiver_type_bobbin, working_hours):
        super().__init__(name, machine_type, receiver_type_bobbin, working_hours)
        self.supported_materials = supported_materials
        self.total_baskets = total_baskets  # MultivareMachine.KM_IN_16_BASKET всего корзин
        self.remaining_basket_length = remaining_basket_length  # MultivareMachine.KM_IN_8_BASKET  # начальный запас длины для 8 корзин
        self.capacity = self.remaining_basket_length
        self.spinners_road = spinners_road

    def is_suitable(self, task):
        return True
        # return material in self.supported_materials and quantity <= self.capacity

    # @classmethod
    # def get_all_instances(cls, names=None):
    #     if names is None:
    #         return list(cls._instances)
    #     return [instance for instance in cls._instances if instance.name in names]

    def __repr__(self):
        return f"MultivareMachine(name={self.equipment_name}, machine_type={self.equipment_type})"


class TwistMachine(Equipment):
    CHANGE_BOBBIN = 5  # смена катушки на мультике
    CHANGE_CRIMP_PAIRS = 12.5

    def __init__(self, name: '', machine_type: [''], recoil_bobbin_type: [''], receiver_type_bobbin, working_hours):
        super().__init__(name, machine_type, receiver_type_bobbin, working_hours)
        self.recoil_bobbin_type = recoil_bobbin_type

    def is_suitable(self, task):
        return (task.equipment_type in self.equipment_type
                and self.recoil_bobbin_type)

    # @classmethod
    # def get_all_instances(cls, names=None):
    #     if names is None:
    #         return list(cls._instances)
    #     return [instance for instance in cls._instances if instance.name in names]

    def __repr__(self):
        return f"MultivareMachine(name={self.equipment_name}, machine_type={self.equipment_type})"


# Функция для инициализации оборудования из JSON файлов
def initialize_equipments():
    equipments = []

    # Загрузка данных из Draggers.json
    with open("res_Equipments/Draggers.json", "r", encoding="utf-8") as dragger_file:
        dragger_data = json.load(dragger_file)
        for name, data in dragger_data.items():
            equipments.append(
                WireDrawingMachine(
                    name, data['equipment_type'], data['supported_materials'], data['basket'],
                    data['spinners_road'], data['min_diameter'], data['max_diameter'], data['receiver_type_bobbin'],
                    data['working_hours']
                    )
                )

    # Загрузка данных из Multivare.json
    with open("res_Equipments/Multivare.json", "r", encoding="utf-8") as multivare_file:
        multivare_data = json.load(multivare_file)
        for name, data in multivare_data.items():
            equipments.append(
                MultivareMachine(
                    name, data['equipment_type'], data['supported_materials'], data['total_baskets'],
                    data['remaining_basket_length'], data['spinners_road'], data['receiver_type_bobbin'],
                    data['working_hours']
                    )
                )

    with open("res_Equipments/Twists.json", "r", encoding="utf-8") as twists_file:
        multivare_data = json.load(twists_file)
        for name, data in multivare_data.items():
            equipments.append(
                TwistMachine(
                    name, data['equipment_type'], data['recoil_bobbin_type'],
                    data['recoil_bobbin_type'], data['working_hours']
                    )
                )

    return equipments
    # print(WireDrawingMachine.get_all_instances())
    # print(MultivareMachine.get_all_instances())


if __name__ == "__main__":
    # Инициализация оборудования
    initialize_equipments()
