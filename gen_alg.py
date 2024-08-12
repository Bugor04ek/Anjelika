import math
import numpy as np
import random

from consts import *
from Оборудование.Strenga import *

from genetika import base
from genetika import creator
from genetika import tools
from genetika import algorithms
import random
import matplotlib.pyplot as plt
import numpy




# Функция для расчета времени перенастройки между заказами мультика
def calculate_setup_time_multivare(previous_order, order):
    total_setup_time = 0
    if previous_order is not None:
        change = False
        if previous_order.spin > order.spin:
            removed_spin = previous_order.spin - order.spin + 1
            total_setup_time += removed_spin * REMOVED_SPIN
            total_setup_time += INSERT_SPIN * order.wires_in_sliver
            change = True
        elif previous_order.spin < order.spin:
            removed_spin = 1
            total_setup_time += removed_spin * REMOVED_SPIN
            total_setup_time += INSERT_SPIN * (order.spin - (previous_order.spin - 1)) * order.wires_in_sliver
            change = True
        dif_wire = abs(order.wires_in_sliver - previous_order.wires_in_sliver)
        if previous_order.wires_in_sliver < order.wires_in_sliver:
            total_setup_time += dif_wire * order.spin * CHANGE_WIRE + STRETCHING_WIRE
            change = True
        elif previous_order.wires_in_sliver > order.wires_in_sliver:
            total_setup_time += dif_wire * previous_order.spin * CHANGE_WIRE
            change = True
        if change:
            total_setup_time += CHANGE_BOBBIN
    return total_setup_time


# Функция для создания матрицы времени перенастроек мультика
def form_matrix_multivare(orders):
    temp_matrix1 = []
    for order1 in orders:
        temp_matrix2 = []
        for order2 in orders:
            temp_matrix2.append(calculate_setup_time_multivare(order1, order2))
        temp_matrix1.append(temp_matrix2)
    return temp_matrix1


# Функция для расчета времени перенастройки для скрутки стренги
def calculate_setup_time_strand(previous_order, order):
    bobbins_previous = previous_order.number_of_strands * 1 if previous_order.full_bobbin[0] == 0 else \
        previous_order.full_bobbin[0]
    bobbins_current = order.number_of_strands * 1 if order.full_bobbin[0] == 0 else order.full_bobbin[0]
    return abs(
        bobbins_previous * REMOVING_CHARGING_BOBBIN + bobbins_current * PREPARING_FOR_LAUNCH + bobbins_current * INSTALLING_CHARGING_BOBBIN)


# Функция для создания матрицы времени перенастроек для скрутки стренги
def form_matrix_strand(orders):
    temp_matrix = []
    for order1 in orders:
        temp_matrix2 = []
        for order2 in orders:
            temp_matrix2.append(calculate_setup_time_strand(order1, order2))
        temp_matrix.append(temp_matrix2)
    return temp_matrix


# Инициализация популяции
def initialize_population(pop_size, num_orders):
    return [np.random.permutation(num_orders) for _ in range(pop_size)]


# Функция приспособленности
def fitness_function(order, time_on_multivare, time_on_strand, setup_time_multivare, setup_time_strand):
    total_time = 0
    # Расчет времени для Multivare
    for i in range(len(order)):
        if i > 0:
            prev_order_idx = order[i - 1]
            curr_order_idx = order[i]
            total_time += setup_time_multivare[prev_order_idx, curr_order_idx]
        total_time += time_on_multivare[order[i]]
    # Расчет времени для Strand Twist
    for i in range(len(order)):
        if i > 0:
            prev_order_idx = order[i - 1]
            curr_order_idx = order[i]
            total_time += setup_time_strand[prev_order_idx, curr_order_idx]
        total_time += time_on_strand[order[i]]
    return total_time


# Функция для селекции родителей на основе турнира
def tournament_selection(population, fitness_values, k=3):
    selected = []
    for _ in range(2):
        tournament = random.sample(list(zip(population, fitness_values)), k)
        winner = min(tournament, key=lambda x: x[1])
        selected.append(winner[0])
    return selected


# Функция для скрещивания двух родителей (однолинейный кроссовер)
def crossover(parent1, parent2):
    size = len(parent1)
    cx_point = random.randint(1, size - 2)
    child1 = list(parent1[:cx_point]) + [gene for gene in parent2 if gene not in parent1[:cx_point]]
    child2 = list(parent2[:cx_point]) + [gene for gene in parent1 if gene not in parent2[:cx_point]]
    return child1, child2


# Функция для мутации (перемешивание двух случайных генов)
def mutate(individual, mutation_rate=0.01):
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            swap_idx = random.randint(0, len(individual) - 1)
            individual[i], individual[swap_idx] = individual[swap_idx], individual[i]


# Основная функция генетического алгоритма
def genetic_algorithm(orders, pop_size=1000, generations=1000, mutation_rate=0.01):
    num_orders = len(orders)
    population = initialize_population(pop_size, num_orders)

    time_on_multivare = np.array([order.time_on_mult for order in orders])
    time_on_strand = np.array([order.order.time_on_streng for order in orders])

    setup_time_multivare = np.array(form_matrix_multivare(orders))
    setup_time_strand = np.array(form_matrix_strand(orders))

    for generation in range(generations):
        fitness_values = [
            fitness_function(order, time_on_multivare, time_on_strand, setup_time_multivare, setup_time_strand) for
            order in population]

        next_population = []
        while len(next_population) < pop_size:
            parents = tournament_selection(population, fitness_values)
            offspring = crossover(parents[0], parents[1])
            mutate(offspring[0], mutation_rate)
            mutate(offspring[1], mutation_rate)
            next_population.extend(offspring)

        population = next_population[:pop_size]
        best_fitness = min(fitness_values)
        print(f"Generation {generation + 1}: Best Fitness = {best_fitness}")

    best_order = population[fitness_values.index(best_fitness)]
    return best_order, best_fitness


# Пример использования
def main(orders: list[TaskForMultik]):
    best_order, best_fitness = genetic_algorithm(orders)
    print("Best order found:")
    print(best_order)
    print("With fitness value:")
    print(best_fitness)
