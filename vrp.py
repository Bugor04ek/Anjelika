"""Simple Travelling Salesperson Problem (TSP) between cities."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from optimization.test import *
from consts import *


def calculate_setup_time(previous_order, order):
    total_setup_time = 0

    if previous_order is not None:

        change = False

        # меньше диаметр - больше фильер
        if previous_order.spin > order.spin:
            removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
            total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
            total_setup_time += INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер
            change = True
        # больше диаметр - меньше фильер
        elif previous_order.spin < order.spin:
            removed_spin = 1  # снимаем последнюю
            total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
            total_setup_time += INSERT_SPIN * (
                    order.spin - (
                    previous_order.spin - 1)) * order.wires_in_sliver  # время на установку фильер +1, потому 1 уже снята tt
            change = True

        """
            2 ПРОВЕРКА -- Разность проволочек
        """

        dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

        if previous_order.wires_in_sliver < order.wires_in_sliver:
            # Надо протянуть новые проволочки через все фильеры на новом заказе
            total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
            change = True
        elif previous_order.wires_in_sliver > order.wires_in_sliver:
            # Надо снять проволочки со всех фильер previous_order
            total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE
            change = True

        if change:
            # Если было любое изменение, то надо сменить катушку
            total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

    return total_setup_time


def form_matrix(orders):
    temp_matrix1 = []

    temp_matrix1.append([0 for _ in range(len(orders) + 1)])
    for order1 in orders:

        temp_matrix2 = [0]
        for order2 in orders:
            temp_matrix2.append(calculate_setup_time(order1, order2))

        temp_matrix1.append(temp_matrix2)

    return temp_matrix1


def create_data_model(orders):
    """Stores the data for the problem."""
    data = {}
    data["order"] = [0]
    for order in orders:
        data["order"].append(order)
    data["order"].append(0)
    data["distance_matrix"] = form_matrix(orders)

    df = pd.DataFrame(data["distance_matrix"])

    mode = "w" if os.path.exists("excel/matrix_time.xlsx") else "a"

    with ExcelWriter("excel/matrix_time.xlsx", mode=mode, engine="openpyxl") as writer:
        df.to_excel(writer)

    data["num_vehicles"] = 1
    data["depot"] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()} минут")
    index = routing.Start(0)
    plan_output = "Route for vehicle 0:\n"
    plan_output_number = ''
    plan_output_group = ''
    plan_output_diameter = ''
    route_distance = 0
    plan_order = []
    while not routing.IsEnd(index):
        plan_output += f" {manager.IndexToNode(index)} ->"
        if isinstance(data['order'][manager.IndexToNode(index)], TaskForMultik):
            plan_output_number += f" {data['order'][manager.IndexToNode(index)].account_number} ->"
            plan_output_diameter += f" {data['order'][manager.IndexToNode(index)].diameter} ->"
            plan_output_group += f" {data['order'][manager.IndexToNode(index)].group} ->"
            plan_order.append(data['order'][manager.IndexToNode(index)])
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += f" {manager.IndexToNode(index)}\n"
    print(plan_output)
    print(plan_output_number)
    print(plan_output_diameter)
    print(plan_output_group)
    plan_output += f"Route distance: {route_distance}минут\n"


def get_routes(solution, routing, manager):
    """Get vehicle routes from a solution and store them in an array."""
    # Get vehicle routes and store them in a two dimensional array whose
    # i,j entry is the jth location visited by vehicle i along its route.
    routes = []
    for route_nbr in range(routing.vehicles()):
        index = routing.Start(route_nbr)
        route = [manager.IndexToNode(index)]
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
        routes.append(route)
    return routes


def main(orders):
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model(orders)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)
        route = get_routes(solution, routing, manager)
        time_change_bobbin(route, data)
        print(*route)

    print(routing.status())


def time_change_bobbin(route, data):
    prev_order = None
    list_orders = []
    for order in route[0]:
        if prev_order is not None:
            if data['order'][prev_order].num_group != data['order'][order].num_group:
                create_solution(list_orders, order.container_capacity, release_date=list_orders[0].release_date)
                list_orders.clear()

        list_orders.append(order)


        prev_order = order
