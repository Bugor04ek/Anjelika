from ortools.linear_solver import pywraplp
import Оборудование.Multivare as Multivare


def create_data_model(orders, container_capacity):
    """Create the data for the example."""
    data = {}
    data["orders"] = orders
    data["items"] = list(range(len(orders)))
    data["bins"] = data["items"]
    data["bin_capacity"] = container_capacity
    return data


def create_solution(orders: list[Multivare.TaskForMultik], container_capacity: float, release_date: object) -> object:
    data = create_data_model(orders, container_capacity)

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")

    if not solver:
        return

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    x = {}
    for i in data["items"]:
        for j in data["bins"]:
            x[(i, j)] = solver.IntVar(0, 1, "x_%i_%i" % (i, j))

    # y[j] = 1 if bin j is used.
    y = {}
    for j in data["bins"]:
        y[j] = solver.IntVar(0, 1, "y[%i]" % j)

    # Constraints
    # Each item must be in exactly one bin.
    for i in data["items"]:
        solver.Add(sum(x[i, j] for j in data["bins"]) == 1)

    # Намотка кабеля не превышает вместимость катушки.
    # Если кабель уже с полной катушкой, то умножаем катушку на вместимость, чтобы влез только один этот кабель
    for j in data["bins"]:
        solver.Add(
            sum(x[(i, j)] * data["orders"][i].full_bobbin[1] if data["orders"][i].full_bobbin[2] == 0
                else x[(i, j)] * data["bin_capacity"] for i in data["items"]) <= y[j] * data["bin_capacity"]
        )

    # Objective: minimize the number of bins used.
    solver.Minimize(solver.Sum([y[j] for j in data["bins"]]))

    status = solver.Solve()
    result = {"orders": [], }
    num_bins = 0
    num_order = 0
    if status == pywraplp.Solver.OPTIMAL:
        for j in data["bins"]:
            if y[j].solution_value() == 1:
                bin_orders = []
                bin_length = 0
                count_order = 0
                bin_dates = []
                # Создает класс катушки, которую набивают кабелями
                bobbin = Multivare.Bobbin(0, data["bin_capacity"], release_date, None)
                for i in data["bins"]:
                    if x[i, j].solution_value() > 0:
                        bin_orders.append(data["orders"][i].account_number)

                        # Если заказа на нескольких катушках, то создаем катушку, заполненную на максимум этим кабелем
                        if data["orders"][i].full_bobbin[2]:
                            # Добавляем в задание на мультике полные катушки с одни кабелем
                            for _ in range(data["orders"][i].full_bobbin[0]):
                                Multivare.check_list_multik.append_bobbin(Multivare.Bobbin(data["bin_capacity"], data["bin_capacity"], data["orders"][i].order.release_date, data["orders"][i]))

                            # Добавляем общему числу катушек заранее просчитанные полные катушки с одним кабелем
                            num_bins += data["orders"][i].full_bobbin[0]

                        bobbin.add(data["orders"][i].full_bobbin[1], data["orders"][i])
                        bin_length += data["orders"][i].full_bobbin[1]  # Используем длину кабеля на неполной катушке
                        count_order += 1
                        num_order += 1
                        bin_dates.append(data["orders"][i].order.release_date)

                Multivare.check_list_multik.append_bobbin(bobbin)

                if bin_orders:
                    num_bins += 1
                    print("Bin number", j)
                    print("  Orders packed:", bin_orders)
                    print("  Намотка:", bin_length)
                    print("  Вместимость катушки:", data['bin_capacity'])
                    print("  Заказов на катушке", count_order)
                    print("  Release dates:", bin_dates)
                    print()
        # print()
        # print("Number of bins used:", num_bins)

        # print("Time = ", solver.WallTime(), " milliseconds")
    else:
        print("The problem does not have an optimal solution.")

    # print("Заказов всего: ", num_order)
    return num_bins
