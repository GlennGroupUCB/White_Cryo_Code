import numpy as np
import visa
import serial
import serial.tools.list_ports
import time

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
	print("connected to: ")
	print(ser.portstr)
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
	print(line)
	i = 0
	s = 0
	e = 1
	for i in range(0, len(line)):	#sparses line to extract pressure
		if line[i] == 'K':			#find begin of press
			s = i+1
		if line[i] == 'E':			#finds end of press and begin of magnitude
			e = i
			pow=int(line[i+2])*-1
			print pow
	torr = float(line[s:e])*10**pow	#final combined pressure in Torr
	print('Pressure: ' + torr + ' Torr')
	

else:
	print "COM7 is not open"


ser.close()
	
