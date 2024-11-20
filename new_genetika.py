from deap import base, creator, tools, algorithms
import random

import Equipments
import Tasks

# Настройка среды DEAP для минимизации времени
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", dict, fitness=creator.FitnessMin)


# Создание начальной популяции на основе заданий
def generate_individual(tasks):
    """Создает индивида с распределением задач по оборудованию."""
    eq = Equipments.MachineMeta.get_all_instances()

    individual = {
        'multivare': [task for task in tasks if isinstance(task, Tasks.MultivareTask)],
        'wiredrawing': [task for task in tasks if isinstance(task, Tasks.WireDrawingTask)]
    }
    return creator.Individual(individual)


def initialize_population(toolbox, tasks, pop_size):
    """Инициализирует популяцию на основе заданий."""
    toolbox.register("individual", tools.initIterate, creator.Individual, lambda: generate_individual(tasks))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    return toolbox.population(n=pop_size)


# Основная функция запуска алгоритма
def run_genetic_algorithm(tasks, pop_size=50, cxpb=0.7, mutpb=0.2, ngen=50):
    toolbox = base.Toolbox()
    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("mate", tools.cxUniform, indpb=0.5)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Инициализация популяции
    population = initialize_population(toolbox, tasks, pop_size)

    # Запуск генетического алгоритма с элитизмом
    algorithms.eaSimple(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=True)

    return population


# Функция оценки приспособленности — для вычисления общего времени выполнения задач
def evaluate_fitness(individual):
    multivare_time = sum(task.time_work for task in individual['multivare'])
    wiredrawing_time = sum(task.time_work for task in individual['wiredrawing'])
    return multivare_time + wiredrawing_time,


def run(tasks):
    run_genetic_algorithm(tasks)