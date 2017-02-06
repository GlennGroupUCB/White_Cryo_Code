import numpy as np
import visa

# program to let you the current and voltages of the agilent power supplies
# the program first checks what the set voltage is 
#if it is set to zero it will just report zero
#other wise you get some non sensical readings for current
#If the voltage is actually set to something then in measures both the voltage and the current
#
#I made the program a definition so we could import it to the temp monitoring program
#the result of that seems to be that it runs one when you import it but oh well
# written by Jordan Wheeler 
# date: 12/9/2016


rm = visa.ResourceManager()



#Change log
def get_temps():
	#form connections to the two lakeshore temperature sensors available
	lk224 = rm.open_resource('GPIB0::12::INSTR') #lakeshore 224
	lk218 = rm.open_resource('GPIB0::2::INSTR') #lakeshore 218
	lr750 = rm.open_resource('GPIB0::4::INSTR') #linear bridge

	#double check that you've connected to the lakeshore temperature sensors by asking them their 		names
	print(lk218.query('*IDN?'))
	print(lk224.query('*IDN?'))
	y = np.ones(17)*(-1)
	y[ 0] = lk218_T1 = float(lk218.query('KRDG?1'))
	#print(y[ 0],lk218_T1)
	y[ 14] = lk218_T2 = float(lk218.query('KRDG?2'))
	y[ 1] = lk218_T3 = float(lk218.query('KRDG?3'))
	y[ 2] = lk218_T5 = float(lk218.query('KRDG?5'))
	y[ 3] = lk218_T6 = float(lk218.query('KRDG?6'))
	y[ 4] = lk218_T8 = float(lk218.query('KRDG?8'))
	
	y[ 5] = lk224_TC2 = float(lk224.query('KRDG? C2'))
	y[ 6] = lk224_TC3 = float(lk224.query('KRDG? C3'))
	y[ 7] = lk224_TC4 = float(lk224.query('KRDG? C4'))
	y[ 8] = lk224_TC5 = float(lk224.query('KRDG? C5'))
	y[ 9] = lk224_TD2 = float(lk224.query('KRDG? D2'))
	y[ 10] = lk224_TD3 = float(lk224.query('KRDG? D3'))
	y[ 11] = lk224_TD5 = float(lk224.query('KRDG? D5'))
	
	y[ 12] = lk224_A = float(lk224.query('KRDG? A'))
	y[ 13] = lk224_B = float(lk224.query('KRDG? B'))
	y[ 16] = lk224_TD1 = float(lk224.query('KRDG? D1'))
	lr750_a = lr750.query('GET 0')
	#print(lr750_a)
	if i == 0: # there is some weirdness where the first call returns an empty string
		lr750_a_temp = -1
	if i != 0:
		try: #every once in a while this fails
			lr750_a_num = np.float(lr750_a[0:8])
			print(lr750_a_num)
			y[ 15] = lr750_a_temp = RX202_interp(-lr750_a_num*1000)
		except:
			y[ 15] = lr750_a_temp = -1.
	return y

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
	
