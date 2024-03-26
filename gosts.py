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
                   "(\-|)(?P<TropicalDesign>T|)"
                   "\s(?P<NumberVeins>[1|3])[x|х]"
                   "(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   "\s(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс)(\/|)(?P<SectionMetalScreen>\d+|)"
                   "-(?P<RatedVoltage>\d+[,|.|]\d+|\d+)",
        'param': {
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
        'pattern': r"(?P<Material>А|)"
                   "(?P<InsulationMaterial>В|Пв|П)"
                   "(?P<Armor>Б|Ба|К|Ка|)"
                   "(?P<OuterShellMaterial>В|Шв|Шп|П)"
                   "(?P<NotArmor>Г|)"
                   "(?P<MetalScreen>Э|)"
                   "(?P<FireDanger>нг|(нг\((AF\/R|[A,А]|B)\)(-LS|-HF|-FRLS|-FRHF))|)"
                   "(?P<Shape>П|)"
                   "(-|)(?P<TropicalDesign>\[T,Т]|)"
                   "\s(?P<NumberVeins>[1-5])[x|х]"
                   "(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   "(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс|)"
                   "((?P<NumberVeinsNPE>\+\d+)[x|х]"
                   "(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)"
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
        'pattern': r"(?P<Wire>СИП)(-|\s)"
                   "(?P<ConstructiveExecution>[1-4]|г)\s"
                   "(?P<NumberVeins>[1-4])[x|х]"
                   "(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   "(\+(?P<NumberVeinsNPE>\d+)[x|х]"
                   "(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)|)-"
                   "(?P<RatedVoltage>0,6\/1|[a-zA-Z0-9][10-20]|35)",
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
        'pattern': r"(?P<ProductType>Пу|Ку)"
                   "(?P<DegreeFlexibility>Г|)"
                   "(?P<InsulationMaterial>В|П|.)"
                   "(?P<OuterShellMaterial>В|П|[^-]|)"
                   "(?P<FireDanger>нг(\(([A,А]|[В,B]|[C,С]|D)\)|)(-LS|-LSLTx|-HF|-HFLTx)|)"
                   "(\-|)(?P<TropicalDesign>[T,Т]|ХЛ|)\s"
                   "(?P<NumberVeins>[1-5])[x|х]"
                   "(?P<NominalSection>\d+[,|.|]\d+|\d+)"
                   "((?P<NumberVeinsNPE>\+\d+)[x|х]"
                   "(?P<NominalSectionNPE>\d+[,|.|]\d+|\d+)|)"
                   "(?P<NPE>(\((N\,PE|PE\,N|PE|N)\))|)",
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
                   r"(?P<InsulationMaterial>Р|ТП|ТПу|В|)"
                   r"(?P<ConstructiveExecution>С|У|[э,Э]|)"
                   r"(?P<OuterShellMaterial>Р|ТП|ТПу|В|)"
                   r"(?P<ConstructiveExecution>С|У|[э,Э]|)"
                   r"(?P<HeatResistance>Тк|Т|)"
                   r"(?P<FireDanger>нг(\(([A,А] F\/R|[A,А]|[В,B]|[C,С]|D)\)|)(-LS|-HF|-FRLS|-FRHF|-LSLTx|-HFLTx|-FRHFLTx)|)"
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
            'Material': 'Материал',
            'Cable': 'Кабель',
            'DegreesFlexibility': 'Степень гибкости',
            'InsulationMaterial': 'Изоляция',
            'OuterShellMaterial': 'Оболочка',
            'ConstructiveExecution': 'Конструктивное исполнение',
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
