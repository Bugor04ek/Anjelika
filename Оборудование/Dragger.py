from Multivare import *


class Basket:

    def __init__(self, orders):
        self.orders: [TaskForMultik] = orders
        self.diameter = 3
        self.len_order = 16_000

    def __add__(self, other):
        self.orders.append(other)


class QueueDragger:

    def __init__(self):
        self.orders = []

    def __add__(self, other):
        self.orders.append(other)


queue_dragger = QueueDragger()
