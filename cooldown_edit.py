from __future__ import print_function
import numpy as np
import visa
import time
import datetime
import os

from functions import get_temps

#########################################################
#      Program to cooldown the cryostat                 #
#########################################################

# we want to just monitor the temperature and when things get cold enough
#turn on the helium 3 and 4 pumps so the can cooldown thoses stages to 4K
# through gas condution

#last time I ran this from start it didn't turn on the pumps. Then I reset the program and it worked fine?

#Change log
#1/11/2016 -Jordan - Added in turning on ADR switch after it gets cold
#12/05/2017 -Tim- Added implementation with functions.py Removed plotting and writing

#use Temp_monitor_edit.py to monitor everything and write data.
#execfile("Temp_monitor_edit.py") #begin monitoring process


Cold_enough = 0
#create a resourcemanager and see what instruments the computer can talk to
rm = visa.ResourceManager()
rm.list_resources()


ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack

#turn on the power supplies 
ag49.write('OUTPut ON')
ag47b.write('OUTPut ON')
ag47t.write('OUTPut ON')

start = time.time() #define a start time

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
		
		
		#cooldown crap starts here
		#the way I am doing it is a bit weird we are just continously looping
		#and excuting certain fridge steps if the time is appropriate
		#rather than just do things step by step. 
		
		if lk224_TC4 < 6.0 and lk224_TC5 < 6.0:
			Cold_enough = 1
			#print("The cyostat is cold enough to turn on the pumps.")

		#Heat up the 4He pump
		if Cold_enough == 1 and lk224_TD5 < 12.: # if the switches have coold and just in case if the 4K plate gets to hot
			#print("test")
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
			
		#Heat up the He3 
		if Cold_enough == 1 and lk224_TD5<12.:
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
		
		# turn on the ADR switch when it gets to cold to conduct
		'''
		if lk224_TD2<26.:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 3.5')#3.5
		if lk224_TD2>30.: #temp should drop slowly
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 2.5')#2.5
		if lk224_TD2>35.: #just in case
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 0')
		'''
		seconds = int(t)
		minutes = int(t/60)
		hours = minutes/60
		if seconds >= 60:
			seconds = int(t-(60*minutes))
		if minutes >= 60:
			minutes = int(t-(3600*minutes))
		print('Cooldown duration: ', hours , ':', minutes, ':', seconds)
		time.sleep(10)	
			
		
			
		
except KeyboardInterrupt:
    pass


print("Human interupted the fridge cycle")