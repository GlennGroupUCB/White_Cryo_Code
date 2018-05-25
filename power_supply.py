from __future__ import print_function
import numpy as np
import visa
import time
import os
import sys

# program to let you call heaters by name and turn them on 
# written by Jordan Wheeler 
# date: 8/29/206
# the syntax for using this is python power_supply.py "He4 pump" 1 
# which will set the helium 4 pump to 1 V
# should up date to have some voltage limits so that we don't over heat things

#Change log
#12/1/16 -Jordan -Added output on before trying to change voltage
#3/10/18 -Jordan -Changed it so that you can call from other python programs

def change_voltage(target,voltage,verbose = False):
	rm = visa.ResourceManager()
	if target == 'He4 pump':
		ag47t = rm.open_resource('GPIB1::15::INSTR') #power supply 3647 on top row of rack
		ag47t.write("OUTput ON")
		ag47t.write('INST:SEL OUT1')#Helium 4 pump
		ag47t.write('Volt ' +str(voltage))
		if verbose == True:
			print('You have tuned on the Helium 4 pump to ' + str(voltage) + ' V')
		#raw_input('Do you want to continue?') # should put some safteys in here
		#turn_off()  
	elif target == 'He3 pump':
		ag47t = rm.open_resource('GPIB1::15::INSTR') #power supply 3647 on top row of rack
		ag47t.write("OUTput ON")
		ag47t.write('INST:SEL OUT2')
		ag47t.write('Volt ' +str(voltage))
		if verbose == True:
			print('You have tuned on the Helium 3 pump to ' + str(voltage) + ' V')
	elif target == 'He4 switch':
		ag47b = rm.open_resource('GPIB1::5::INSTR') #power supply 3647 on bottom row of power supplies
		ag47b.write("OUTput ON")
		ag47b.write('INST:SEL OUT1')
		ag47b.write('Volt ' +str(voltage))
		if verbose == True:
			print('You have tuned on the Helium 4 switch to ' + str(voltage) + ' V')
	elif target == 'He3 switch':
		ag47b = rm.open_resource('GPIB1::5::INSTR') #power supply 3647 on bottom row of power supplies
		ag47b.write("OUTput ON")
		ag47b.write('INST:SEL OUT2')
		ag47b.write('Volt ' +str(voltage))
		if verbose == True:
			print('You have tuned on the Helium 3 switch to ' + str(voltage) + ' V')
	elif target == 'ADR switch':
		ag49 = rm.open_resource('GPIB1::3::INSTR') #power supply 3649 in the upper RH of Rack
		ag49.write("OUTput ON")
		ag49.write('INST:SEL OUT1')
		ag49.write('Volt ' +str(voltage))
		if verbose == True:
			print('You have tuned on the ADR switch to ' + str(voltage) + ' V')
	elif target == '4K 1K switch':
		ag49 = rm.open_resource('GPIB1::3::INSTR') #power supply 3649 in the upper RH of Rack
		ag49.write("OUTput ON")
		ag49.write('INST:SEL OUT2')
		ag49.write('Volt ' +str(voltage))
		if verbose == True:
			print('You have tuned on the 4K - 1K to ' + str(voltage) + ' V')
	else:
		print('You have selected a target that does not exist.')
		sys.exit()


if __name__=='__main__': #if you want to call it from command line
	if len(sys.argv) < 3:
		print('Provide a target string and a voltage')
		print('targets are He4 pump, He3 pump, He4 switch, He3 switch, ADR switch, 4K 1K switch')
		sys.exit()
	else:	
		voltage = float(sys.argv[2])
		target = sys.argv[1]
		change_voltage(target,voltage,verbose = True)
		sys.exit()
		
		