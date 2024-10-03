import re

GOSTS = {
    '55025-2012': {
        'pattern': r"(?P<Material>А|)"
                   r"(?P<InsulationMaterial>В|Пв|)"
                   r"(?P<Armor>Б|Ба|К|Ка|)"
                   r"(?P<OuterShellMaterial>В|П|Пу)"
                   r"(?P<NotArmor>Г|)"
                   r"(?P<FireDanger>нг|(нг\((AF\/R|A|B)\)(-LS|-HF|))|)"
                   r"(?P<SealingElements>г|2г|ж|$|)"
                   r"(\-|)(?P<TropicalDesign>T|)"
                   r"\s(?P<NumberVeins>[1|3])[x|х]"
                   r"(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   r"(\s(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс)(\/|)(?P<SectionMetalScreen>\d+|)-(?P<RatedVoltage>\d+[,|.|]\d+|\d+)|)",
        'param': {
            'Material': 'Material',
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
        'pattern': r"(?P<Material>А|)"
                   r"(?P<InsulationMaterial>В|Пв|П)"
                   r"(?P<Armor>Б|Ба|К|Ка|)"
                   r"(?P<OuterShellMaterial>В|Шв|Шп|П)"
                   r"(?P<NotArmor>Г|)"
                   r"(?P<MetalScreen>Э|)"
                   r"(?P<FireDanger>нг|(нг\((AF\/R|[A,А]|B)\)((-LS|-HF|-FRLS|-FRHF)|))|(нг(-LS|-HF|-FRLS|-FRHF))|)"
                   r"(?P<Shape>П|)"
                   r"(-|)(?P<TropicalDesign>\[T,Т]|)"
                   r"\s(?P<NumberVeins>[1-5])[x|х]"
                   r"(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   r"(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс|)"
                   r"((?P<NumberVeinsNPE>\+\d+)[x|х](?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)(?P<ConstructiveExecutionMetalScreenNPE>ок|ос|мк|мс|)|)"
                   r"(?P<NPE>(\((N\,PE|PE|N)\))|)"
                   r"(-(?P<RatedVoltage>0,66|1|3)|)",
        'param': {
            'Material': 'Material',
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
        'pattern': r"(?P<Material>)"
                   r"(?P<Wire>СИП)(-|\s)"
                   r"(?P<ConstructiveExecution>[1-4]|г)\s"
                   r"(?P<NumberVeins>[1-4])[x|х]"
                   r"(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   r"(\+(?P<NumberVeinsNPE>\d+)[x|х]"
                   r"(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)|)-"
                   r"(?P<RatedVoltage>0,6\/1|[a-zA-Z0-9][10-20]|35)",
        'param': {
            'Material': 'Material',
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
        'pattern': r"(?P<ProductType>Пу|Ку)"
                   r"(?P<DegreeFlexibility>Г|)"
                   r"(?P<InsulationMaterial>В|П|.)"
                   r"(?P<OuterShellMaterial>В|П|[^-]|)"
                   r"(?P<FireDanger>нг(\(([A,А]|[В,B]|[C,С]|D)\)|)(-LS|-LSLTx|-HF|-HFLTx)|)"
                   r"(\-|)(?P<TropicalDesign>[T,Т]|ХЛ|)\s"
                   r"(?P<NumberVeins>[1-5])[x|х]"
                   r"(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   r"((?P<NumberVeinsNPE>\+\d+)[x|х]"
                   r"(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)|)"
                   r"(?P<NPE>(\((N\,PE|PE\,N|PE|N)\))|)",
        'param': {
            'ProductType': 'Тип продукта',
            'DegreeFlexibility': 'Степень гибкости',
            'InsulationMaterial': 'Изоляция',
            'OuterShellMaterial': 'Оболочка',
            'FireDanger': 'Пожарная опасность',
            'TropicalDesign': 'Тропическое исполнение',
            'NumberVeins': 'Количество жил',
            'NominalSection': 'Номинальное сечение',
            'NumberVeinsNPE': 'Количество жил NPE',
            'NominalSectionNPE': 'Номинальное сечение NPE',
            'NPE': 'NPE',
        }
    },
    '24334-2020': {
        'pattern': r"(?P<Material>Ас|)"
                   r"(?P<Cable>К)"
                   r"(?P<DegreesFlexibility>Г|ПГ|ОГ)"
                   r"(?P<InsulationMaterial>Р|П|ТП|ТПу|В|)"
                   r"(?P<ConstructiveExecution1>С|У|[э,Э]|)"
                   r"(?P<OuterShellMaterial>Р|П|ТП|ТПу|В|)"
                   r"(?P<ConstructiveExecution2>С|У|[э,Э]|)"
                   r"(?P<HeatResistance>Тк|Т|)"
                   r"(?P<FireDanger>нг(\(([A,А] F\/R|[A,А]|[В,B]|[C,С]|D)\)|)(-LS|-HF|-FRLS|-FRHF|-LSLTx|-HFLTx|-FRHFLTx|)|)"
                   r"(-|)(?P<TropicalDesign>\[T,Т]|ХЛ|)\s"
                   r"(?P<NumberVeins>\d+)[x|х]"
                   r"(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   r"(?P<NPE>(\((N\,PE|PE|N)\))|)"
                   r"(\+(?P<NumberVeinsNPE>\d+)[x|х]"
                   r"(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)"
                   r"(\((?P<NPE2>N\,PE|PE\,N|PE|N)\)|)|)"
                   r"(\s|)(?P<RatedVoltage>\d+\/\d+|)"
                   r"(-|)(?P<OperatingMode>\d|)",
        'param': {
            'Material': 'Material',
            'Cable': 'Кабель',
            'DegreesFlexibility': 'Степень гибкости',
            'InsulationMaterial': 'Изоляция',
            'ConstructiveExecution1': 'Конструктивное исполнение',
            'OuterShellMaterial': 'Оболочка',
            'ConstructiveExecution2': 'Конструктивное исполнение',
            'HeatResistance': 'Термостойкость',
            'FireDanger': 'Пожарная опасность',
            'TropicalDesign': 'Тропическое исполнение',
            'NumberVeins': 'Количество жил',
            'NominalSection': 'Номинальное сечение',
            'NPE': 'NPE',
            'NumberVeinsNPE': 'Количество жил NPE',
            'NominalSectionNPE': 'Номинальное сечение NPE',
            'NPE2': 'NPE',
            'RatedVoltage': 'Номинальное напряжение',
            'OperatingMode': 'Рабочий режим',
        }
    },
    '7399-97': {
        'pattern': r"(?P<Mark>ШОГ|ШОГ-С|ШВП|ШВД|ШВВП|ШВЛ|ПВС|ПВСн|ПВСП|ШРО|ПРС|ПРМ|ПСГ|ШВП|ШОГ|ШВП)"
                   r"(-|)(?P<TropicalDesign>[T,Т]|УХЛ|У|)\s"
                   r"(?P<NumberVeins>\d+)[x|х]"
                   r"(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   r"(\+(?P<NumberVeinsNPE>\d+)[x|х]"
                   r"(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)(\)|)|)"
                   r"(\s|)(?P<RatedVoltage>\d+|)",
        'param': {
            'Mark': 'Марка',
            'TropicalDesign': 'Тропическое исполнение',
            'NumberVeins': 'Количество жил',
            'NominalSection': 'Номинальное сечение',
            'NumberVeinsNPE': 'Количество жил NPE',
            'NominalSectionNPE': 'Номинальное сечение NPE',
            'RatedVoltage': 'Номинальное напряжение',

        }
    },
}


def type_definition(self, mark):
    for gosts in GOSTS.keys():
        res = re.search(GOSTS[gosts]['pattern'], mark, flags=0)

        if res is not None:
            self.cable_decryption(res, gosts)
            break


def cable_decryption(self, result, gosts):
    name_groups = GOSTS[gosts]['param']

    print(gosts)

    for group in name_groups:
        if result.group(group) != '' and result.group(group) is not None:
            self.cable_Parameters[name_groups[group]] = result.group(group)
