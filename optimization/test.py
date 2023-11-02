import pulp

# Создайте объект задачи оптимизации
problem = pulp.LpProblem("CablePacking", pulp.LpMaximize)
reel_length = 32,365
length11 = 20.4
length12 = 30.6
length13 = 1.5
length14 = 20.4
length15 = 20.2
length16 = 15.3

# Определите переменные для количество каждого кабеля на каждой катушке
# Для каждой катушки и каждого кабеля создайте переменную, которая определяет количество этого кабеля на катушке
x11 = pulp.LpVariable("x11", lowBound=0, cat='Integer')  # Количество кабеля 1 на катушке 1
x12 = pulp.LpVariable("x12", lowBound=0, cat='Integer')  # Количество кабеля 2 на катушке 1
x13 = pulp.LpVariable("x14", lowBound=0, cat='Integer')  # Количество кабеля 3 на катушке 1
x14 = pulp.LpVariable("x14", lowBound=0, cat='Integer')  # Количество кабеля 4 на катушке 1
x15 = pulp.LpVariable("x15", lowBound=0, cat='Integer')  # Количество кабеля 5 на катушке 1
x16 = pulp.LpVariable("x16", lowBound=0, cat='Integer')  # Количество кабеля 6 на катушке 1


# Определите целевую функцию: максимизация общей длины намотки
problem += (x11 * length11 + x12 * length12 + x13 * length13 + x14 * length14 + x15 * length15 + x16 * length16), "Total Cable Length"

# Ограничения на доступную длину намотки на каждой катушке
problem += (x11 * length11 <= reel_length, "Reel 1 Length Constraint")
problem += (x12 * length12 <= reel_length, "Reel 2 Length Constraint")
problem += (x13 * length13 <= reel_length, "Reel 3 Length Constraint")
problem += (x14 * length14 <= reel_length, "Reel 4 Length Constraint")
problem += (x15 * length15 <= reel_length, "Reel 5 Length Constraint")
problem += (x16 * length16 <= reel_length, "Reel 6 Length Constraint")

# Добавьте ограничения для других катушек

# Ограничения на количество кабелей каждого типа
problem += (x11 * length11 + x12 * length12 + x13 * length13 + x14 * length14 + x15 * length15 + x16 * length16 <= reel_length, "Cable Count Constraint")

problem.solve()

print("Status:", pulp.LpStatus[problem.status])
print("Total Cable Length =", pulp.value(problem.objective))
print("Optimal solution:")
print("x11 =", x11.varValue)
print("x12 =", x12.varValue)
# Выведите результаты для других переменных