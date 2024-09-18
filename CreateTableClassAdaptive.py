
import genetika
import vrp
from consts import *

from optimization.calculate_bobbin import *
import Оборудование.Dragger as Dragger

file_name = 'excel/Заказы.xlsx'


def formation_of_orders_in_the_date_range(orders: list[TaskForMultik], date_range: int, groups_by_dates: dict):
    """
    Формирование заказов в диапазоне дат
    :return:
    """

    min_date = orders[0].order.release_date

    for i in range(1, len(orders)):
        if (orders[i].order.release_date - min_date).days > date_range:
            groups_by_dates[min_date] = orders[0:i]
            formation_of_orders_in_the_date_range(orders[i:], date_range, groups_by_dates)
            break
    else:
        groups_by_dates[min_date] = orders
        return


def sort_date(order):
    return order.order.release_date


def forming_file_with_groups(arr_orders: list[TaskForMultik]):
    # Загрузка существующего файла Excel
    existing_file = 'excel/output_class.xlsx'

    groups = max(order.num_group for order in arr_orders)  # максимальное число групп, для количества листов

    # Извлекаем заголовки столбцов
    headers = ["Номер счета", "Марка", "Дата выпуска", "Длина кабеля, км", "Километраж", "Время на мультике",
               "Длина стренг", "Барабаны (Кол-во полных катушек, Объем на частичной катушки)", "Параметры", "Группа",
               "Количество фильер"]
    data_res = []
    bin = 0

    print("Хотите компоновать на катушки кабели в пределах даты?"
          "\n1. Да"
          "\n2. Нет")
    k = int(input())

    if k == 1:
        date_range = int(input('Введите диапазон дат: '))

    sort_orders = sorted(arr_orders, key=sort_date)
    for group in range(groups + 1):
        # Инициализируем пустой список для хранения данных
        data = []
        # Извлекаем данные из PrettyTable и добавляем их в список
        data = [order for order in sort_orders if order.num_group == group]

        container_capacity = data[0].volume_bobbin

        if k == 1:
            groups_by_dates = {}
            formation_of_orders_in_the_date_range(data, date_range, groups_by_dates)

            for key in groups_by_dates.keys():
                bin += create_solution(groups_by_dates[key], container_capacity, release_date=key)
            else:
                groups_by_dates.clear()
        else:
            bin += create_solution(data, container_capacity, release_date=data[0].order.release_date)

        data.append('')
        data_res.extend(data)
        data.clear()

    print("Всего катушек", bin)

    # Возвращаем массив с готовыми группами, чтобы рассчитать время
    return data_res


def forming_file_with_groups_excel(arr_orders: list[TaskForMultik]):
    # Загрузка существующего файла Excel
    existing_file = 'excel/output_class.xlsx'

    groups = max(order.num_group for order in arr_orders)  # максимальное число групп, для количества листов

    # Извлекаем заголовки столбцов
    headers = ["Номер счета", "Марка", "Дата выпуска", "Длина кабеля, км", "Километраж", "Время на мультике",
               "Длина стренг", "Барабаны (Кол-во полных катушек, Объем на частичной катушки)", "Параметры", "Группа",
               "Количество фильер"]
    data_res = []

    for group in range(groups + 1):
        # Инициализируем пустой список для хранения данных
        data = []
        # Извлекаем данные из PrettyTable и добавляем их в список
        for order in sorted(arr_orders, key=sort_date):
            if order.num_group == group:
                data.append(
                    [order.account_number, order.order.mark.mark, order.order.release_date, order.length_strands,
                     order.volume_bobbin, order.time_on_mult, order.length_strands, order.full_bobbin,
                     order.group, order.num_group, order.spin])
                container_capacity = order.volume_bobbin

        # pack_cables(data, container_capacity)
        data.append('')
        data_res.extend(data)
        data.clear()
        # Создаем DataFrame из списка данных и заголовков

    df = pd.DataFrame(data_res, columns=headers)

    mode = "w" if os.path.exists(existing_file) else "a"

    with ExcelWriter(existing_file, mode=mode, engine="openpyxl") as writer:
        df.to_excel(writer)


def create_orders():
    """
    Создание 2 таблиц:
    1. Основная, содержащая информацию о заказе
    2. Таблица с параметрами для вычисления "Длина куска 1 корзины"
    :return: result_table -- результирующая таблица с вычисленным столбцом "Длина куска 1 корзины"
    """
    # A - IDZak
    # B - Номер счета
    # C - Марка
    # D - Дата выпуска по заказу
    # E - Количество километров в производство
    # F - Количество жил
    # G - Перед мультиком -> d_mult = 2.08
    # H - Диаметр проволоки
    # I - Количество стренг
    # J - Кол-во прядей (количество зарядных катушек на стренге)
    # K - Кол-во проволок в пряди (количество проволок одной пряди)
    # L - Кол-во прядей доп
    # M - Кол-во проволок доп
    # N - Вид барабана
    # O - Количество заправок
    # P - Километраж масса VS Длина
    # Q - Время на мультике

    excel_data = pd.read_excel(file_name, sheet_name="Лист5")
    excel_data['Дата выпуска по заказу'] = pd.to_datetime(excel_data['Дата выпуска по заказу'],
                                                          format='%d.%m.%Y').dt.date
    data = pd.DataFrame(excel_data).fillna(0)
    orders = list()

    for row in data.values:
        orders.append(Order(IDZak=row[0], account_number=row[1], mark=row[2], release_date=row[3], order_length=row[4],
                            number_of_veins=row[5], diameter=row[7], number_of_strands=row[8], number_of_sliver=row[9],
                            wires_in_sliver=row[10], number_of_sliver_extra=row[11], wires_in_sliver_extra=row[12],
                            number_of_veins_plus=row[13], diameter_plus=row[14], number_of_strands_plus=row[15],
                            number_of_sliver_plus=row[16],
                            wires_in_sliver_plus=row[17], number_of_sliver_extra_plus=row[18],
                            wires_in_sliver_extra_plus=row[19],
                            number_of_veins_support=row[20], diameter_support=row[21],
                            number_of_strands_support=row[22], number_of_sliver_support=row[23],
                            wires_in_sliver_support=row[24], number_of_sliver_extra_support=row[25],
                            wires_in_sliver_extra_support=row[26],
                            type_bobbin=row[27], volume_bobbin=row[28], time_on_dragger=row[29], time_on_multivare=row[30], time_on_streng=row[31]))

    return orders


if __name__ == "__main__":
    orders = create_orders()
    print(*TaskForMultik.orders, sep='\n')
    # result = forming_file_with_groups(TaskForMultik.orders)
    # check_list_multik.output_in_excel()
    #
    # vrp.main(TaskForMultik.orders)
    # gen_alg.main(TaskForMultik.orders)

    genetika.main_multivare(TaskForMultik.orders)

    print(Dragger.queue_dragger, sep='\n')
    print(Dragger.queue_dragger.num_basket)
    print(Multivare.QueueMultivare.rest_basket)
    print(Multivare.QueueMultivare.rest_orders)

    genetika.main_dragger(Dragger.queue_dragger.queue)


