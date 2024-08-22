class QueueDragger:

    def __init__(self):
        self.orders = []

    def __add__(self, other):
        self.orders.append(other)


queue_dragger = QueueDragger()
