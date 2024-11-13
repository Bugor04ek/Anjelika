import pandas as pd
import json

# Загружаем файл Excel
file_path = "Пути на старую волочилку.xlsx"  # Укажите путь к вашему файлу Excel
sheet_name = "Лист1"  # Укажите имя листа, если нужно
df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")

# Преобразуем данные
routes = {}

for _, row in df.iterrows():
    final_diameter = str(row["13"]).replace(",", ".")  # Итоговый диаметр как ключ
    filter_chain = []

    # Создаем маршрут с фильерами, пропуская пустые значения и заменяя запятые на точки
    for column in df.columns[1:-1]:  # Пропускаем первую и последнюю колонку
        value = row[column]
        if pd.notna(value):
            filter_chain.append(float(str(value).replace(",", ".")))

    # Добавляем маршрут в общий список для данного диаметра
    if final_diameter not in routes:
        routes[final_diameter] = []
    routes[final_diameter].append(filter_chain)

# Сохраняем в JSON файл
output_file = "../Оборудование/routes.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(routes, f, ensure_ascii=False, indent=4)

print(f"Данные успешно сохранены в {output_file}")
