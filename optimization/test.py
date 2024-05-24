from ortools.linear_solver import pywraplp
from scipy.optimize import minimize
from consts import *
from Multik import *


def create_data_model(orders, container_capacity):
    """Create the data for the example."""
    data = {}
    data["orders"] = orders
    data["items"] = list(range(len(orders)))
    data["bins"] = data["items"]
    data["bin_capacity"] = container_capacity
    return data


def create_solution(orders: list[TaskForMultik], container_capacity: float, release_date: object) -> object:
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

    # The amount packed in each bin cannot exceed its capacity.
    for j in data["bins"]:
        solver.Add(
            sum(x[(i, j)] * data["orders"][i].full_bobbin[1] for i in data["items"])
            <= y[j] * data["bin_capacity"]
        )

    # for i in data["items"]:
    #     if data["orders"][i].full_bobbin[2]:
    #         solver.Add(sum(x[i, j] for j in data["bins"]) == 1)
    #
    # for j in data["bins"]:
    #     solver.Add(
    #         sum(x[(i, j)] * data["orders"][i].full_bobbin[0] for i in data["items"]) <= 0
    #     )

    for j in data["bins"]:
        solver.Add(
            sum(x[(i, j)] * data["orders"][i].full_bobbin[2] for i in data["items"])
            <= y[j] * 2
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
                # orders = []
                bin_length = 0
                count_order = 0
                bin_dates = []
                bobbin = Bobbin(0, data["bin_capacity"], release_date, None)
                check_list_multik.append(bobbin)
                for i in data["bins"]:
                    if x[i, j].solution_value() > 0:
                        bin_orders.append(data["orders"][i].account_number)
                        bobbin.add(data["orders"][i].full_bobbin[1], data["orders"][i])
                        # orders.append(data["orders"][i].account_number)
                        bin_length += data["orders"][i].full_bobbin[1]  # Используем длину кабеля на неполной катушке
                        count_order += 1
                        num_order += 1
                        bin_dates.append(data["orders"][i].order.release_date)
                if bin_orders:
                    num_bins += 1
                    print("Bin number", j)
                    print("  Orders packed:", bin_orders)
                    print("  Total length:", bin_length)
                    print("  Заказов на катушке", count_order)
                    print("  Release dates:", bin_dates)
                    print()
        print()
        print("Number of bins used:", num_bins)

        print("Time = ", solver.WallTime(), " milliseconds")
    else:
        print("The problem does not have an optimal solution.")

    print("Заказов всего: ", num_order)
    return num_bins
