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
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack

#print(ag49.query('VOLTAGE?')) #ask what the voltage is 
#ag49.write('VOLTAGE 15') #change it to 15V
#print(ag49.query('VOLTAGE?')) #ask again to make sure it changed

ag49.write('OUTPut ON')# this must be the 4K heater
ag47b.write('OUTPut ON')#pump heat switches 
ag47t.write('OUTPut ON')#these are the pump heaters

#ag49.write('INST:SEL OUT2')
#ag49.write('Volt 1')

#time.sleep(20)


ag49.write('*rst;*cls')
ag49.close()
ag47b.write('*rst;*cls')
ag47b.close()
ag47t.write('*rst;*cls')
ag47t.close()
