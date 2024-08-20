import Оборудование.Multivare as Multivare


class Basket:

    def __init__(self, orders):
        self.orders: [Multivare.TaskForMultik] = orders
        self.diameter = 3
        self.len_order = 16_000

    def __add__(self, other):
        self.orders.append(other)

    def __repr__(self):
        return "'%s'" % self.orders


class QueueDragger:

    def __init__(self):
        self.orders = []

    def __add__(self, other):
        self.orders.append(other)


queue_dragger = QueueDragger()
