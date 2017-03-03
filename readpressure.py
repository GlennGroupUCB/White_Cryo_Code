import numpy as np
import visa
import serial
import serial.tools.list_ports
import time

# Connect to Pressure Gauge (900USB-1 @ COM4)
ser = serial.Serial( 		#initialize
	port = 'COM4',\	
	baudrate = 115200,\
	parity=serial.PARITY_NONE,\
	stopbits=serial.STOPBITS_ONE,\
    	bytesize=serial.EIGHTBITS,\
        	timeout=1)
	
print("connected to: " + ser.portstr)
    
#this will store the line
seq = []
count = 1

while True:
    for c in ser.read():
        seq.append(chr(c)) #convert from ANSCII
        joined_seq = ''.join(str(v) for v in seq) #Make a string from array

        if chr(c) == '\n':
            print("Line " + str(count) + ': ' + joined_seq)
            seq = []
            count += 1
            break


ser.close()
	
