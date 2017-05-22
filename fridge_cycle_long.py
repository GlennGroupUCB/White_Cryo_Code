from __future__ import print_function
import numpy as np
import visa
import matplotlib
import datetime
import os
import time
from functions import get_temps

#########################################################
#      Program to cycle the Chase fridge                #
#########################################################



#CHANGE LOG
# 5/15/17 -Tim- added implementation with functions.py Removed plotting and writing


#use Temp_monitor_edit.py to monitor everything and write data.
#execfile("Temp_monitor_edit.py") #begin monitoring process

#create a resourcemanager and see what instruments the computer can talk to
rm = visa.ResourceManager()
rm.list_resources()

ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack

#turn on the power supplys 
ag49.write('OUTPut ON')
ag47b.write('OUTPut ON')
ag47t.write('OUTPut ON')


start = time.time() #define a start time

k = 0
i = 0
finished = 0 #run until it looks like the fridge cycle has completed

try: #allows you to kill the loop with ctrl c
	while finished == 0: #count the seconds since the start time, and sleep for 1 second between each count
		
		t = time.time()-start
		
		
		#grab temperatures and store them to the temperature array	
		temps = get_temps()
		y = temps
		
		lk218_T1 = y[0]
		lk218_T2 = y[1]
		lk218_T3 = y[2]
		lk218_T4 = y[3]
		lk218_T5 = y[4]
		lk218_T6 = y[5]
		lk218_T8 = y[6]
	
		lk224_TC2 = y[7]
		lk224_TC3 = y[8]
		lk224_TC4 = y[9]
		lk224_TC5 = y[10]
		lk224_TD1 = y[11]
		lk224_TD2 = y[12]
		lk224_TD3 = y[13]
		lk224_TD4 = y[14]
		lk224_TD5 = y[15]
		lk224_A = y[16]
		lk224_B = y[17]
		lr750_a_temp = y[18]
		
	
		
		#fridge cycle crap starts here
		#the way I am doing it is a bit weird we are just continously looping
		#and excuting certain fridge steps if the time is appropriate
		#rather than just do things step by step. 
		#step 1 is open (heat) the ADR switch
		
		# ADR heat switch want to leave open so that the 1K head can cool the ADR
		# but turn off before cycle ADR
		# doesn't cool well if the 4K-1K switch is not on and the film burner is hot
		'''
        if t>120*60 and t<180*60: #70,800
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 1.75')#3.5
		else:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 0')
		'''		
		#Heat up the 4He pump
		if t>0*60 and t<100*60:
			if lk224_TC2<45.:
				ag47t.write('INST:SEL OUT1')
				ag47t.write('Volt 25')
			if lk224_TC2>45.:
				ag47t.write('INST:SEL OUT1')
				ag47t.write('Volt 15') #should creep up
			if lk224_TC2>50.:
				ag47t.write('INST:SEL OUT1')
				ag47t.write('Volt 0')	
		else:
			ag47t.write('INST:SEL OUT1')
			ag47t.write('Volt 0')
			
		#Heat up the He3 pump turn off 50mins after He4 pump is turned off
		if t>60*60 and t<200*60:
			if lk224_TC3<45.:
				ag47t.write('INST:SEL OUT2')
				ag47t.write('Volt 15')
			if lk224_TC3>45.:
				ag47t.write('INST:SEL OUT2')
				ag47t.write('Volt 5')#should increase slowly
			if lk224_TC3>50.:
				ag47t.write('INST:SEL OUT2')
				ag47t.write('Volt 0')
		else:
			ag47t.write('INST:SEL OUT2')
			ag47t.write('Volt 0')
			
		#close (heat) the He4 switch turn on when He4 pump is turned off leave on forever
		if t>100*60 and t<300*60:
			if lk224_TC4<29.:
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 4')
			if lk224_TC4>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 2')
			if lk224_TC4>35.: #just in case
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 0')
		elif t>300*60 and lk224_A<0.5: #keep the switches on until the 300mK stage heats up
			if lk224_TC4<29.:
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 4')
			if lk224_TC4>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 2')
			if lk224_TC4>35.: #just in case
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 0')
		else:
			ag47b.write('INST:SEL OUT1')
			ag47b.write('Volt 0')
			
		#close (heat) the He3 switch turn on when He3 pump is turned off leave on forever
		if t>100*60 and t<300*60:
			if lk224_TC5<30.:
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 3.6')
			if lk224_TC5>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 2')
			if lk224_TC5>35.: #just in case
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 0')
		elif t>300*60 and lk224_A<0.5: #keep the switchs on until 300mK stage warms up
			if lk224_TC5<30.:
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 3.6')
			if lk224_TC5>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 2')
			if lk224_TC5>35.: #just in case
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 0')	
		else:
			ag47b.write('INST:SEL OUT2')
			ag47b.write('Volt 0')
			
		#monitor when the 300mK stage heats up.
		if t>300*60:
			if lk224_A>0.5:
				print("fridge cycle complete")
				k = k+1
				
		if k>60.: #keep logging for another hour
			finished = 1
		
		seconds = int(t)
		minutes = int(t/60)
		hours = minutes/60
		if seconds >= 60:
			seconds = int(t-(60*minutes))
		if minutes >= 60:
			minutes = int(t-(3600*minutes))
		print('Cycle duration: ', hours , ':', minutes, ':', seconds)
		time.sleep(10)
		
except KeyboardInterrupt:
    pass



print("Human interupted the fridge cycle")