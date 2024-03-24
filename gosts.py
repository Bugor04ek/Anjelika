import re

GOSTS = {
    '55025-2012': {
        'pattern': r"(?P<Material>А|)"
                   "(?P<InsulationMaterial>В|Пв|)"
                   "(?P<Armor>Б|Ба|К|Ка|)"
                   "(?P<OuterShellMaterial>В|П|Пу)"
                   "(?P<NotArmor>Г|)"
                   "(?P<FireDanger>нг|(нг\((AF\/R|A|B)\)(-LS|-HF|))|)"
                   "(?P<SealingElements>г|2г|ж|$|)"
                   "(?P<TropicalDesign>\-T|)"
                   "\s(?P<NumberVeins>[1|3])[x|х]"
                   "(?P<NominalSection>16|25|35|50|70|95|120|150|185|240|300|400|500|625|630|800|1000|1200|1400|1600)"
                   "\s(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс)(\/|)(?P<SectionMetalScreen>\d+|)"
                   "-(?P<RatedVoltage>6|10|15|20|30|35)",
        'param':
            {
                'Material': 'Материал',
                'InsulationMaterial': 'Изоляция',
                'Armor': 'Бронированный',
                'OuterShellMaterial': 'Оболочка',
                'NotArmor': 'Небронированный',
                'FireDanger': 'Пожарная опасность',
                'SealingElements': 'Герметизирующий элемент',
                'TropicalDesign': 'Тропическое исполнение',
                'NumberVeins': 'Количество жил',
                'NominalSection': 'Номинальное сечение',
                'ConstructiveExecutionMetalScreen': 'Конструктивное исполнение',
                'SectionMetalScreen': 'Cечение металлического экрана',
                'RatedVoltage': 'Номинальное напряжение',
            }
    },
    '31996-2012': {
        'pattern': "(?P<Material>А|)"
                   "(?P<InsulationMaterial>В|Пв|П)"
                   "(?P<Armor>Б|Ба|К|Ка|)"
                   "(?P<OuterShellMaterial>В|Шв|Шп|П)"
                   "(?P<NotArmor>Г|)"
                   "(?P<MetalScreen>Э|)"
                   "(?P<FireDanger>нг|(нг\((AF\/R|[A,А]|B)\)(-LS|-HF|-FRLS|-FRHF))|)"
                   "(?P<Shape>П|)"
                   "(?P<TropicalDesign>\-[T,Т]|)"
                   "\s(?P<NumberVeins>[1-5])[x|х]"
                   "(?P<NominalSection>1,5|2,5|4|6|10|16|25|35|50|70|95|120|150|185|240|300|400|500|625|630|800|1000)"
                   "(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс|)"
                   "((?P<NumberVeinsNPE>\+\d+)[x|х]"
                   "(?P<NominalSectionNPE>1,5|2,5|4|6|10|16|25|35|50|70|95|120|150|185|240|300|400|500|625|630|800|1000)"
                   "(?P<ConstructiveExecutionMetalScreenNPE>ок|ос|мк|мс)|)"
                   "(?P<NPE>(\((N\,PE|PE|N)\))|)"
                   "-(?P<RatedVoltage>0,66|1|3)",
        'param': {
                'Material': 'Материал',
                'InsulationMaterial': 'Изоляция',
                'Armor': 'Бронированный',
                'OuterShellMaterial': 'Оболочка',
                'NotArmor': 'Небронированный',
                'MetalScreen': 'Металлический экран',
                'FireDanger': 'Пожарная опасность',
                'Shape': 'Форма',
                'TropicalDesign': 'Тропическое исполнение',
                'NumberVeins': 'Количество жил',
                'NominalSection': 'Номинальное сечение',
                'ConstructiveExecutionMetalScreen': 'Конструктивное исполнение металлического экрана',
                'NumberVeinsNPE': 'Количество жил NPE',
                'NominalSectionNPE': 'Номинальное сечение NPE',
                'ConstructiveExecutionMetalScreenNPE': 'Конструктивное исполнение NPE',
                'NPE': 'NPE',
                'RatedVoltage': 'Номинальное напряжение',
            }
    },
    '31946-2012': {
        'pattern': {
            '(?P<Wire>СИП)-'
            '(?P<ConstructiveExecution>[1-4]|г)\s'
            '(?P<NumberVeins>[1-4])[x|х]'
            '(?P<NominalSection>16|25|35|50|70|95|120|150|185|240)'
            '(\+(?P<NumberVeinsNPE>\d+)[x|х]'
            '(?P<NominalSectionNPE>25|35|50|54[,|\.]6|70|95)|)-'
            '(?P<RatedVoltage>0,6\/1|[[:alnum:]][10-20]|35)'
        },
        'param': {
            'Wire': 'Провод',
            'ConstructiveExecution': 'Конструктивное исполнение',
            'NumberVeins': 'Количество жил',
            'NominalSection': 'Номинальное сечение',
            'NumberVeinsNPE': 'Количество жил NPE',
            'NominalSectionNPE': 'Номинальное сечение NPE',
            'RatedVoltage': 'Номинальное напряжение',
        }
},
    '31947-2012': {
        'pattern': {
            "(?P<ProductType>Пу|Ку)"
            "(?P<DegreeFlexibility>Г|)"
            "(?P<InsulationMaterial>В|П|.)"
            "(?P<ShellMaterial>В|П|.|)"
            "(?P<FireDanger>нг\(([A,А]|[В,B]|[C,С]|D)\)(-LS|-LSLTx|-HF|-HFLTx)|)"
            "(?P<TropicalDesign>\-[T,Т]|-ХЛ|)\s"
            "(?P<NumberVeins>[1-5])[x|х]"
            "(?P<NominalSection>0,5|0,75|1,0|1,5|2,5|4|6|10|16|25|35|50|70|95|120|150|185|240|300|400)"
            "((?P<NumberVeinsNPE>\+\d+)[x|х]"
            "(?P<NominalSectionNPE>0,5|0,75|1,0|1,5|2,5|4|6|10|16|25|35|50|70|95|120|150|185|240|300|400)|)"
            "(?P<NPE>(\((N\,PE|PE\,N|PE|N)\))|)"
        },
        'param':
        {
            'ProductType': 'Тип продукта',
            'DegreeFlexibility': 'Степень гибкости',
            'InsulationMaterial': 'Изоляция',
            'ShellMaterial': 'Номинальное сечение',
            'FireDanger': 'Количество жил NPE',
            'TropicalDesign': 'Номинальное сечение NPE',
            'NumberVeins': 'Номинальное напряжение',
            'NominalSection': 'Тип продукта',
            'NumberVeinsNPE': 'Степень гибкости',
            'NominalSectionNPE': 'Изоляция',
            'NPE': 'Номинальное сечение',
        }
},
}


def type_definition(mark: str):

    for gosts in GOSTS.keys():
        res = re.search(GOSTS[gosts]['pattern'], mark, flags=0)

        if res is not None:
            break

    cable_decryption(res, gosts)


def cable_decryption(result, gosts):

    name_groups = GOSTS[gosts]['param']

    print(gosts)

    for group in name_groups:
        if result.group(group) != '':
            print(name_groups[group], result.group(group))


if __name__ == "__main__":
    cable = "ПвБШп-Т 5х240мс(N,PE)-1"
    type_definition(cable)
