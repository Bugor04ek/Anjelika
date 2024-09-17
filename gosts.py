import re

GOSTS = {
    '55025-2012':{
        'pattern': r"(?'Material'А|)(?'InsulationMaterial'В|Пв|)(?'Armor'Б|Ба|К|Ка|)(?'OuterShellMaterial'В|П|Пу)"
              "(?'NotArmor'Г|)(?'FireDanger'нг|(нг\((AF\/R|A|B)\)(-LS|-HF|))|)(?'SealingElements'г|2г|ж|$|)"
              "(?'TropicalDesign'\-T|)\s(?'NumberVeins'[1|3])[x|х]"
              "(?'NominalSection'16|25|35|50|70|95|120|150|185|240|300|400|500|625|630|800|1000|1200|1400|1600)\s"
              "(?'ConstructiveExecutionMetalScreen'ок|ос|мк|мс)(?'MetalScreen'\/\d+|)-(?'RatedVoltage'6|10|15|20|30|35)",
        'параметры':
        {
            'Материал': "(?'Материал'А|)",
            'Изоляция': "(?'Изоляция'В|Пв|)",
            'Броня': "(?'Броня'Б|Ба|К|Ка|)",
            'Оболочка': "(?'OuterShellMaterial'В|П|Пу)",
        }
    }
}

if __name__=="__main__":
    cabel = "ПвБВнг(A)-LS 3x240 мс/25-10"

    for gosts in GOSTS.keys():
        res = re.search("(?P<Material>А|)(?P<InsulationMaterial>В|Пв|)(?P<Armor>Б|Ба|К|Ка|)(?P<OuterShellMaterial>В|П|Пу)(?P<NotArmor>Г|)(?P<FireDanger>нг|(нг\((AF\/R|A|B)\)(-LS|-HF|))|)(?P<SealingElements>г|2г|ж|$|)(?P<TropicalDesign>\-T|)\s(?P<NumberVeins>[1|3])[x|х](?P<NominalSection>16|25|35|50|70|95|120|150|185|240|300|400|500|625|630|800|1000|1200|1400|1600)\s(?P<ConstructiveExecutionMetalScreen>ок|ос|мк|мс)(?P<MetalScreen>\/\d+|)-(?P<RatedVoltage>6|10|15|20|30|35)", cabel, flags=0)