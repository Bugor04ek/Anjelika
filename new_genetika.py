from deap import base, creator, tools, algorithms
import random
import numpy as np
import matplotlib.pyplot as plt
import datetime
import Оборудование.Multivare as Multivare
import Оборудование.Dragger as Dragger

# Константы генетического алгоритма
POPULATION_SIZE = 200  # Размер популяции
P_CROSSOVER = 0.8  # Вероятность скрещивания
P_MUTATION = 0.2  # Вероятность мутации
MAX_GENERATIONS = 50  # Число поколений


# Создаем типы для минимизации
creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))  # добавлено для мультизадачности
creator.create("Individual", dict, fitness=creator.FitnessMin)

# Инструменты DEAP
toolbox = base.Toolbox()

# Количество заданий для мультика и волочилки
NUM_TASKS_MULTIVARE = 10
NUM_TASKS_WIREDRAWING = 10


# Генерируем случайный порядок заданий для каждого оборудования
def random_task_order():
    return {
        "multivare": random.sample(range(NUM_TASKS_MULTIVARE), NUM_TASKS_MULTIVARE),
        "wiredrawing": random.sample(range(NUM_TASKS_WIREDRAWING), NUM_TASKS_WIREDRAWING)
    }


toolbox.register("individual", tools.initIterate, creator.Individual, random_task_order)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


# Заглушка для оценки
def evaluate(individual):
    multivare_order = individual["multivare"]
    wiredrawing_order = individual["wiredrawing"]

    # Здесь добавим расчет времени для мультика и волочилки
    # Примерные заглушки:
    multivare_time = sum(multivare_order)  # временная оценка
    wiredrawing_time = sum(wiredrawing_order)  # временная оценка

    # Показатель: чем меньше простои и общее время, тем лучше
    total_time = multivare_time + wiredrawing_time
    return total_time, 100  # Второй элемент — место для штрафа за простои


toolbox.register("evaluate", evaluate)

# Регистрация операций для алгоритма
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.2)

# Создаем популяцию
population = toolbox.population(n=POPULATION_SIZE)

# Статистика
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("min", np.min)
stats.register("avg", np.mean)

# Запуск генетического алгоритма с журналом
start = datetime.datetime.now()

population, logbook = algorithms.eaSimple(
    population, toolbox,
    cxpb=P_CROSSOVER, mutpb=P_MUTATION,
    ngen=MAX_GENERATIONS, stats=stats, verbose=True
)

# Анализ результатов
minFitnessValues, meanFitnessValues = logbook.select("min", "avg")
end = datetime.datetime.now()

# Отображаем время работы
print("Время работы:", end - start)

# График минимального и среднего значений функции приспособленности
plt.plot(minFitnessValues, color='red')
plt.plot(meanFitnessValues, color='green')
plt.xlabel('Поколение')
plt.ylabel('Мин/средняя приспособленность')
plt.title('Зависимость минимальной и средней приспособленности от поколения')
plt.show()