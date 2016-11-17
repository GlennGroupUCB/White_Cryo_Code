import visa

rm = visa.ResourceManager()
rm.list_resources()

ag49 = rm.open_resource('GPIB0::3::INSTR')
ag49.write('OUTPut OFF')