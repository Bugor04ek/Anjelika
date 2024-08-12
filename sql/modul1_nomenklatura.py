import pyodbc
import const
from gosts import *

cable_parameters = {}


def type_definition(mark):
    """
    Берем каждый гост из справочника и проверяем марку на каждый патерн.
    После того как найдем подходящий гост вызываем cable_decryption, передаем найденный результат и гост
    """
    for gosts in GOSTS.keys():
        res = re.search(GOSTS[gosts]['pattern'], mark, flags=0)

        if res is not None:
            cable_decryption(mark, res, gosts)
            break
    # else:
    # print(mark, 'не определена')


def cable_decryption(mark, result, gosts):
    """
    Забираем из справочника гостов все параметры по совпавшему госту (gosts).
    Затем выводим все параметры по совпавшим группам и записываем в справочник класса
    """
    name_groups = GOSTS[gosts]['param']
    cable_parameters['Марка'] = mark
    temp_dict = {}
    for group in name_groups:
        if result.group(group) != '' and result.group(group) is not None:
            temp_dict[name_groups[group]] = result.group(group)

    cable_parameters[mark] = temp_dict


connectionString = f'DRIVER={{SQL Server}};SERVER={const.SERVER};DATABASE={const.DATABASE};UID={const.USERNAME};PWD={const.PASSWORD};'
conn = pyodbc.connect(connectionString, Trusted_connection=True)

cur = conn.cursor()

cur.execute(
    '''
WITH RECURSIVE CTE AS (
    -- Начальная часть: найти все папки "ГОСТ", находящиеся непосредственно внутри папок "СИП"
    SELECT f1._Code, f1._Description, f1._ParentID
    FROM _Reference368X1 f1
    JOIN _Reference368X1 f2 ON f1._ParentID = f2._Code
    WHERE f1._Description LIKE 'ГОСТ%' AND f2._Description LIKE 'СИП%'

    UNION ALL

    -- Рекурсивная часть: найти всех потомков папок "ГОСТ"
    SELECT f3._Code, f3._Description, f3._ParentID
    FROM _Reference368X1 f3
    JOIN CTE ON f3._ParentID = CTE._Code
)
SELECT * FROM CTE
UNION
-- Включить начальные папки ГОСТ
SELECT f1._Code, f1._Description, f1._ParentID
FROM _Reference368X1 f1
JOIN _Reference368X1 f2 ON f1._ParentID = f2._Code
WHERE f1._Description LIKE 'ГОСТ%' AND f2._Description LIKE 'СИП%';
'''
    # ''' ВВГ
    #     select _Description from _Reference368X1 where _ParentIDRRef =
    #     (select _IDRRef from _Reference368X1 where _Code = '00000001671')
    # '''
)
result = cur.fetchall()

for mark in result:
    type_definition(mark[0])

conn.close()
