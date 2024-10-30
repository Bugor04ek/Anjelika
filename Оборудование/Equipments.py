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
