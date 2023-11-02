import pulp

# создать список всех возможных таблиц
# Первый параметр количество кабелей
# Второй размер катушки
possible_tables = [tuple(c)for c in pulp.allcombinations(guests,max_table_size)]

# создайте двоичную переменную, указывающую, что используется параметр таблицы
x = pulp.LpVariable.dicts(
    "table", possible_tables, lowBound=0, upBound=1, cat=pulp.LpInteger
)

seating_model = pulp.LpProblem("Wedding Seating Model", pulp.LpMinimize)

seating_model += pulp.lpSum([happiness(table) * x[table] for table in possible_tables])