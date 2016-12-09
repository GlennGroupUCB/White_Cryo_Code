import numpy as np
import visa

# program to let you the current and voltages of the agilent power supplies
# the program first checks what the set voltage is 
#if it is set to zero it will just report zero
#other wise you get some non sensical readings for current
#If the volatage is actually set to something then in measures both the voltage and the current
#
#I made the program a definition so we could import it to the temp monitoring program
#the result of that seems to be that it runs one when you import it but oh well
# written by Jordan Wheeler 
# date: 12/9/2016


#Change log



def read_power_supplies():

	labels = ("He4 pump", "He3 pump", "He4 switch", "He3 switch", "ADR switch", "4K 1K switch")


	rm = visa.ResourceManager()
	ag47t = rm.open_resource('GPIB0::15::INSTR')
	ag47b = rm.open_resource('GPIB0::5::INSTR')
	ag49 = rm.open_resource('GPIB0::3::INSTR') 

	volt = np.zeros(6)
	curr = np.zeros(6)

	ag47t.write('INST:SEL OUT1')
	ag47t.write('volt?')
	if np.float(ag47t.read()) == 0:
		volt[0] = 0
		curr[0] = 0
	else:
		ag47t.write('Meas:volt?')
		volt[0] = np.abs(np.float(ag47t.read()))
		ag47t.write('Meas:Curr?')
		curr[0] = np.abs(np.float(ag47t.read()))
	ag47t.write('INST:SEL OUT2')
	ag47t.write('volt?')
	if np.float(ag47t.read()) == 0:
		volt[1] = 0
		curr[1] = 0
	else:
		ag47t.write('Meas:volt?')
		volt[1] = np.abs(np.float(ag47t.read()))
		ag47t.write('Meas:Curr?')
		curr[1] = np.abs(np.float(ag47t.read()))

	ag47b.write('INST:SEL OUT1')
	ag47b.write('volt?')
	if np.float(ag47b.read()) == 0:
		volt[2] = 0
		curr[2] = 0
	else:
		ag47b.write('Meas:volt?')
		volt[2] = np.abs(np.float(ag47b.read()))
		ag47b.write('Meas:Curr?')
		curr[2] = np.abs(np.float(ag47b.read()))
	ag47b.write('INST:SEL OUT2')
	ag47b.write('volt?')
	if np.float(ag47b.read()) == 0:
		volt[3] = 0
		curr[3] = 0
	else:
		ag47b.write('Meas:volt?')
		volt[3] = np.abs(np.float(ag47b.read()))
		ag47b.write('Meas:Curr?')
		curr[3] = np.abs(np.float(ag47b.read()))

	ag49.write('INST:SEL OUT1')
	ag49.write('volt?')
	if np.float(ag49.read()) == 0:
		volt[4] = 0
		curr[4] = 0
	else:
		ag49.write('Meas:volt?')
		volt[4] = np.abs(np.float(ag49.read()))
		ag49.write('Meas:Curr?')
		curr[4] = np.abs(np.float(ag49.read()))
	ag49.write('INST:SEL OUT2')
	ag49.write('volt?')
	if np.float(ag49.read()) == 0:
		volt[5] = 0
		curr[5] = 0
	else:
		ag49.write('Meas:volt?')
		volt[5] = np.abs(np.float(ag49.read()))
		ag49.write('Meas:Curr?')
		curr[5] = np.abs(np.float(ag49.read()))
	return labels, volt, curr

labels, volt, curr = read_power_supplies()

for i in range(0,len(volt)):
	print(labels[i]+" " +str(volt[i])[0:4] + "V  "+ str(curr[i])[0:6]+ "A")
	
