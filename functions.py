import numpy as np
import visa
import serial
import serial.tools.list_ports

#added
import matplotlib
matplotlib.use('qt4agg')#need for continuously updating plot


#Contains function which read pressure, temperture, voltage and current from intruments as well as plotting and writing to file.
#designed to be implemented in Temp_monitor.py
#Created by Tim Childers in March 2017

#ChangeLog:
# 03/10/17 - Added get_press() to read and return pressure from 972B DualMag Transducer - Tim
# 03/15/17 - Changed timeout of get_press() to 0.1 sec to minimize delay. Can't go under 0.1 sec without throwing error - Tim
# 04/10/17 - added plot_and_write() function for use with fast monitor - Tim

#initializes plot resources for temperature
def initialize():
	# this is just some stuff i use to cycle thorugh plot line styles/colors
	lines = ['-','--','-.']
	colors = ['b','g','r','c','m','y','k']

	#labels for the thermometers extra space is so the numbers all line up. might be a better way to add the space
	labels = ['4K P.T.               ','4K HTS             ','50K HTS           ','Black Body       ','50K P.T.            ','50K Plate         ','ADR Shield      ','4He Pump        ','3He Pump        ','4He Switch        ','3He Switch        ','300 mK Shield   ','ADR Switch        ','4-1K Switch       ','1K Shield           ','4K Plate           ','3He Head          ','4He Head          ','ADR                   ']


	#allows you to not plot ugly thermometers
	plots = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18)

	return lines, colors, labels, plots




#create a resourcemanager and see what instruments the computer can talk to
#path = os.path.normpath("C:/Program Files/IVI Foundation/VISA/Win64/Lib_x64/msc/visa64.lib")
rm = visa.ResourceManager()
print rm.list_resources()

def get_press():
	# Connect to Pressure Gauge (900USB-1 @ COM7)
	ser = serial.Serial( 		#initialize
	port = 'COM7',
	baudrate = 115200,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout= 2
	)

	#print(ser.portstr)
	if ser.is_open:
		#print("connected to: ")
		#print(ser.portstr)
		#ser.write('@254AD?;FF')		#finds device address '253'

		#pressdata = ser.read(10)	#read 10 lines of data
		#line = ser.readline()
		#print(pressdata)
		#print(line)

		#ser.write('@253PR1?;FF') #non combined reading
		#line = ser.readline()
		#print(line)
		ser.write('@253PR4?;FF') #combined reading, 4 digits
		line = ser.readline()
		#print(line)
		i = 0
		s = 0
		e = 1
		for i in range(0, len(line)):	#sparses line to extract pressure
			if line[i] == 'K':			#find begin of press
				s = i+1
			if line[i] == 'E':			#finds end of press and begin of magnitude
				e = i
				pow=int(line[i+2])*-1
				#print pow
		mBar = float(line[s:e])*1.33322*10**pow	#final combined pressure in mbar
		print('Pressure: ' + str(mBar) + ' mbar')


	else:
		print "COM7 is not open"


	ser.close()
	return mBar



def get_temps():
	#form connections to the two lakeshore temperature, and one resistance devices available
	lk224 = rm.open_resource('GPIB0::12::INSTR') #lakeshore 224
	lk218 = rm.open_resource('GPIB0::2::INSTR') #lakeshore 218
	lr750 = rm.open_resource('GPIB0::4::INSTR') #linear bridge

	#double check that you've connected to the lakeshore temperature sensors by asking them their 		names
	#print(lk218.query('*IDN?'))
	#print(lk224.query('*IDN?'))
	y = np.ones(19)*(-1)
	#print(y[ 0],lk218_T1)
	y[ 0] = lk218_T1 = float(lk218.query('KRDG?1'))
	y[ 1] = lk218_T2 = float(lk218.query('KRDG?2'))
	y[ 2] = lk218_T3 = float(lk218.query('KRDG?3'))
	y[ 3] = lk218_T4 = float(lk218.query('KRDG?4'))
	y[ 4] = lk218_T5 = float(lk218.query('KRDG?5'))
	y[ 5] = lk218_T6 = float(lk218.query('KRDG?6'))
	y[ 6] = lk218_T8 = float(lk218.query('KRDG?8'))

	y[ 7] = lk224_TC2 = float(lk224.query('KRDG? C2'))
	y[ 8] = lk224_TC3 = float(lk224.query('KRDG? C3'))
	y[ 9] = lk224_TC4 = float(lk224.query('KRDG? C4'))
	y[ 10] = lk224_TC5 = float(lk224.query('KRDG? C5'))
	y[ 11] = lk224_TD1 = float(lk224.query('KRDG? D1'))
	y[ 12] = lk224_TD2 = float(lk224.query('KRDG? D2'))
	y[ 13] = lk224_TD3 = float(lk224.query('KRDG? D3'))                                       ▬
	y[ 14] = lk224_TD4 = float(lk224.query('KRDG? D4'))
	y[ 15] = lk224_TD5 = float(lk224.query('KRDG? D5'))

	y[ 16] = lk224_A = float(lk224.query('KRDG? A'))
	y[ 17] = lk224_B = float(lk224.query('KRDG? B'))

	lr750_a = lr750.query('GET 0')
	
	try: #every once in a while this fails
		lr750_a_num = np.float(lr750_a[0:8])
			print(lr750_a_num)
		y[ 18] = lr750_a_temp = RX202_interp(-lr750_a_num*1000)
	except:
			y[ 18] = lr750_a_temp = -1.
	
	return y


# program to let you the current and voltages of the agilent power supplies
# the program first checks what the set voltage is
#if it is set to zero it will just report zero
#other wise you get some non sensical readings for current
#If the voltage is actually set to something then in measures both the voltage and the current
# written by Jordan Wheeler
# date: 12/9/2016
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
