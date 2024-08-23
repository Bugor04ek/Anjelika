import Оборудование.Multivare as Multivare


class QueueDragger:

    def __init__(self):
        self.orders = []

    def __add__(self, other):
        self.orders.append(other)

    def __str__(self):
        res = ''

        for orders in self.orders:
            if issubclass(Multivare.Basket, type(orders)):
                res += 'Корзина (Время работы заказов = {}ч. {}мин.): {}'.format(str(orders.time_work // 60), str(round(orders.time_work % 60, 2)), orders.__str__())

        return res + '\n'


queue_dragger = QueueDragger()
