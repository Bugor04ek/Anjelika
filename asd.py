from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from consts import *


def calculate_setup_time(previous_order, order):

    total_setup_time = 0

    if previous_order is not None:
        # меньше диаметр - больше фильер
        if previous_order.spin > order.spin:
            removed_spin = previous_order.spin - order.spin + 1  # снимаем фильеры +1, чтобы переставить ее в конец
            total_setup_time += removed_spin * REMOVED_SPIN  # Время на снятие фильер
            total_setup_time += INSERT_SPIN * order.wires_in_sliver  # Время на установку фильер
            total_setup_time += CHANGE_BOBBIN  # Время на смену катушки
        # больше диаметр - меньше фильер
        elif previous_order.spin < order.spin:
            removed_spin = 1  # снимаем последнюю
            total_setup_time += removed_spin * REMOVED_SPIN  # время на снятие фильер
            total_setup_time += INSERT_SPIN * (order.spin - previous_order.spin - 1) * order.wires_in_sliver  # время на установку фильер -1, потому 1 уже снята
            total_setup_time += CHANGE_BOBBIN  # Время на смену катушки

        """
            2 ПРОВЕРКА -- Разность проволочек
        """

        dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)

        if previous_order.wires_in_sliver < order.wires_in_sliver:
            # Надо протянуть новые проволочки через все фильеры на новом заказе
            total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
        elif previous_order.wires_in_sliver > order.wires_in_sliver:
            # Надо снять проволочки со всех фильер previous_order
            total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE

    return total_setup_time


def create_data_model(orders: list[TaskForMultik]):
    """Stores the data for the problem."""
    data = {}
    data["order"] = [0]
    for order in orders:
        data["order"].append(order)
    data["order"].append(0)
    data["distance_matrix"] = form_matrix(orders)
    # data["demands"] = [order.length_piece for order in orders]
    # data["vehicle_capacities"] = [15, 15, 15, 15]
    data["depot"] = 0

    # groups = max(order.num_group for order in orders)  # максимальное число групп, для количества листов
    # container_capacity = []
    # for group in range(groups + 1):
    #     data1 = [order for order in orders if order.num_group == group]
    #     container_capacity.append(data1[0].volume_bobbin)
    #
    # data["num_vehicles"] = len(container_capacity)
    # data["vehicle_capacities"] = container_capacity

    return data


def form_matrix(orders):

    temp_matrix1 = []

    temp_matrix1.append([0 for _ in range(len(orders) + 1)])
    for order1 in orders:

        temp_matrix2 = [0]
        for order2 in orders:
            temp_matrix2.append(calculate_setup_time(order1, order2) + order2.time_on_mult)

        temp_matrix1.append(temp_matrix2)

    return temp_matrix1


# def print_solution(data, manager, routing, solution):
#     """Prints solution on console."""
#     print(f"Objective: {solution.ObjectiveValue()}")
#     total_distance = 0
#     total_load = 0
#     for vehicle_id in range(data["num_vehicles"]):
#         index = routing.Start(vehicle_id)
#         plan_output = f"Route for vehicle {vehicle_id}:\n"
#         route_distance = 0
#         route_load = 0
#         while not routing.IsEnd(index):
#             node_index = manager.IndexToNode(index)
#             route_load += data["demands"][node_index]
#             plan_output += f" {node_index} Load({route_load}) -> "
#             previous_index = index
#             index = solution.Value(routing.NextVar(index))
#             route_distance += routing.GetArcCostForVehicle(
#                 previous_index, index, vehicle_id
#             )
#         plan_output += f" {manager.IndexToNode(index)} Load({route_load})\n"
#         plan_output += f"Distance of the route: {route_distance}m\n"
#         plan_output += f"Load of the route: {route_load}\n"
#         print(plan_output)
#         total_distance += route_distance
#         total_load += route_load
#     print(f"Total distance of all routes: {total_distance}m")
#     print(f"Total load of all routes: {total_load}")

# def print_solution(data, manager, routing, solution):
#     """Prints solution on console."""
#     print(f"Objective: {solution.ObjectiveValue()}")
#     max_route_distance = 0
#     for vehicle_id in range(data["num_vehicles"]):
#         index = routing.Start(vehicle_id)
#         plan_output = f"Route for vehicle {vehicle_id}:\n"
#         route_distance = 0
#         plan_output_number = ''
#         plan_output_diameter = ''
#         plan_order = []
#         while not routing.IsEnd(index):
#             plan_output += f" {manager.IndexToNode(index)} -> "
#             if isinstance(data['order'][manager.IndexToNode(index)], TaskForMultik):
#                 plan_output_number += f" {data['order'][manager.IndexToNode(index)].account_number} ->"
#                 plan_output_diameter += f" {data['order'][manager.IndexToNode(index)].diameter} ->"
#                 plan_order.append(data['order'][manager.IndexToNode(index)])
#
#             previous_index = index
#             index = solution.Value(routing.NextVar(index))
#             route_distance += routing.GetArcCostForVehicle(
#                 previous_index, index, vehicle_id
#             )
#         plan_output += f"{manager.IndexToNode(index)}\n"
#         plan_output += f"Distance of the route: {route_distance}m\n"
#         print(plan_output)
#         print(plan_output_number)
#         print(plan_output_diameter)
#         max_route_distance = max(route_distance, max_route_distance)
#     print(f"Maximum of the route distances: {max_route_distance}m")

def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()} miles")
    index = routing.Start(0)
    plan_output = "Route for vehicle 0:\n"
    plan_output_number = ''
    plan_output_diameter = ''
    route_distance = 0
    plan_order = []
    while not routing.IsEnd(index):
        plan_output += f" {manager.IndexToNode(index)} ->"

        if isinstance(data['order'][manager.IndexToNode(index)], TaskForMultik):
            plan_output_number += f" {data['order'][manager.IndexToNode(index)].account_number} ->"
            plan_output_diameter += f" {data['order'][manager.IndexToNode(index)].diameter} ->"
            plan_order.append(data['order'][manager.IndexToNode(index)])

        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += f" {manager.IndexToNode(index)}\n"
    print(plan_output)
    print(plan_output_number)
    print(plan_output_diameter)
    plan_output += f"Route distance: {route_distance}минут\n"
    # print(*plan_order, sep='\n')


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

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print("No solution found !")


if __name__ == "__main__":
    main()