from __future__ import print_function
import numpy as np
import visa
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib

#create a resourcemanager and see what instruments the computer can talk to
rm = visa.ResourceManager()
rm.list_resources()

ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
#ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
#ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack

#print(ag49.query('VOLTAGE?')) #ask what the voltage is 
#ag49.write('VOLTAGE 15') #change it to 15V
#print(ag49.query('VOLTAGE?')) #ask again to make sure it changed

ag49.write('OUTPut ON')# this must be the 4K heater
#ag47b.write('OUTPut ON')#pump heat switches 
#ag47t.write('OUTPut ON')#these are the pump heaters
print("waiting")
time.sleep(90*60) #wait for time in seconds Let wait for 30mins between
ag49.write('INST:SEL OUT2')
ag49.write('Volt 0.6')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between
ag49.write('INST:SEL OUT2')
ag49.write('Volt 0')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between
ag49.write('INST:SEL OUT2')
ag49.write('Volt 0.6')
time.sleep(15*60) #wait for time in seconds Let wait for 30mins between
ag49.write('INST:SEL OUT2')
ag49.write('Volt 0.4')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between
ag49.write('INST:SEL OUT2')
ag49.write('Volt 0.3')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between
a49.write('INST:SEL OUT2')
ag49.write('Volt 0.2')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between
a49.write('INST:SEL OUT2')
ag49.write('Volt 0.1')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between
a49.write('INST:SEL OUT2')
ag49.write('Volt 0.0')
time.sleep(30*60) #wait for time in seconds Let wait for 30mins between


#ag47b.write('INST:SEL OUT2')
#ag47b.write('Volt 4')

#ag49.write('INST:SEL OUT2')
#ag49.write('Volt 1')

#ag47b.write('OUTPut OFF')#pump heat switches 


#voltages are
# 1V = 0.1W
# 2V = 0.4W
# 3V = 0.9W
# 3.5V = 1.225W
# 4V = 1.6W
#time.sleep(5) #wait for time in seconds Let wait for 30mins between


ag49.write('*rst;*cls')
ag49.close()
#ag47b.write('*rst;*cls')
#ag47b.close()
#ag47t.write('*rst;*cls')
#ag47t.close()
