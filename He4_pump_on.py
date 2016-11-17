from __future__ import print_function
import numpy as np
import visa
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib

rm = visa.ResourceManager()
rm.list_resources()
ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag49.write('OUTPut ON')
ag47t.write('OUTPut ON')
ag47b.write('OUTPut ON')

		#Heat up the 4He pump
while True:
	if lk224_TC2<40.:
		ag47t.write('INST:SEL OUT1')
		ag47t.write('Volt 20')
	if lk224_TC2>40.:
		ag47t.write('INST:SEL OUT1')
		ag47t.write('Volt 15') #should creep up
	if lk224_TC2>45.:
		ag47t.write('INST:SEL OUT1')
		ag47t.write('Volt 0')
	time.sleep(10)
