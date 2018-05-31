from __future__ import print_function
import numpy as np
import visa
import matplotlib
#matplotlib.use('qt4agg')
matplotlib.use('TkAgg') #seems to be more responsive and less glitchy than gt4agg
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib
import matplotlib.gridspec as gridspec
from functions import read_power_supplies, get_temps, initialize
from scipy import interpolate
import sys
from monitor_plot import MonitorPlot

#########################################################
#      Program to cycle the Chase fridge                #
#########################################################



#CHANGE LOG
#8/7/17 - Added menu to prompt user for start time and adr switch
#1/23/18 -Jordan putting finished back in for the while loop so that it can auto trigger ADR.py when it is done
#1/25/18 - Jordan made it so instead of sleeping until starting the fridge cycle it just starts at t<0 and
# 			doesn't do anything until t=0
#5/31/18 - Sean - Integrated the new MonitorPlot class into this script

finished = 0

t_cool_He3_pump = 160.

def menu():
	global adrOn
	global sleep_time
	userInput = raw_input('Enter time till start: ("hours","minutes")')
	hours_minutes = userInput.split(',')
	hrs = hours_minutes[0]
	mnts = hours_minutes[1]
	sleep_time = int(hrs)*3600 + int(mnts)*60
	adrOn = raw_input('Cycle ADR? "Y" or "N" (CAPITALIZATION IS IMPORTANT): ')
	#return sleep_time

menu()
#time.sleep(sleep_time)

#create a resourcemanager and see what instruments the computer can talk to
rm = visa.ResourceManager()
rm.list_resources()

ag49 = rm.open_resource('GPIB1::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47b = rm.open_resource('GPIB1::5::INSTR') #power supply 3647 on bottom row of power supplies
ag47t = rm.open_resource('GPIB1::15::INSTR') #power supply 3647 on top row of rack

#turn on the power supples
ag49.write('OUTput ON')
ag47b.write('OUTPut ON')
ag47t.write('OUTPut ON')

RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#202 ADR sensor look up table
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False) # interpolates the temperature when in between lookup table values

#initialize plot resources from functions
lines, colors, labels, plots = initialize()

# turn on alarm on for certain values
Alarm_on = np.array((0,#4K P.T.               
	0,#	4K HTS             
	0,#	50K HTS           
	0,#	Black Body      
	0,#	50K P.T.          
	0,#	50K Plate        
	0,#	ADR Shield   
	0,#	4He Pump       
	0,#	3He Pump       
	0,#	4He Switch     
	0,#	3He Switch     
	0,#	300 mK Shield  
	0,#	ADR Switch     
	0,#	4-1K Switch 
	0,#	1K Shield          
	0,#	4K Plate           
	0,#	3He Head         
	0,#	4He Head        
	0))#ADR
Alarm_value =np.array((0,#4K P.T.               
	0,#	4K HTS             
	0,#	50K HTS           
	0,#	Black Body      
	0,#	50K P.T.          
	0,#	50K Plate        
	0,#	ADR Shield   
	0,#	4He Pump       
	0,#	3He Pump       
	0,#	4He Switch     
	0,#	3He Switch     
	0,#	300 mK Shield  
	0,#	ADR Switch     
	0,#	4-1K Switch 
	0,#	1K Shield          
	6.5,#	4K Plate           
	0,#	3He Head         
	0,#	4He Head        
	0))#ADR

sleep_interval = 10. #seconds change back
Alarm = 0 # 0 for off 1 for on

now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
file_prefix =  "./Temps/" + date_str
file_suffix = ''
file_prefix2 =  "./Voltage_Current/" + date_str
file_suffix2 = ''

#do a check to make sure the  he3 and he4 switches have cooled
temps = get_temps()
if temps[9] >15. or temps[10]>15:
	print("He4 or He3 switch still hot waiting at least 20mins to cool")
	if sleep_time<20*60 and sleep_time>-1:
		sleep_time = 20*60

# Create and open the monitoring plot
monitor_plot = MonitorPlot(sleep_interval, 420, plot_pressure=False)
monitor_plot.show()

start = time.time()+sleep_time #define a start time here if we have a delay we just start at t<0
if os.path.isfile(file_prefix + '_temps_fridgecycle.txt') == True: #check if there is already a file with the prefix we are trying to use
	#If a file already exists add a suffix to the end that consist of the time it was created so it can be distinguished from the original file
	file_suffix = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
f = open(file_prefix + file_suffix +'_temps_fridgecycle.txt' ,'w') #open a file to write the temperatures to

if os.path.isfile(file_prefix2 + '_VI_fridgecycle.txt') == True:
	file_suffix2 = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
g = open(file_prefix2 + file_suffix2 +'_VI_fridgecycle.txt' ,'w')


i = 0 #initialize a counter
k = 0
try: #allows you to kill the loop with ctrl c
	while finished == 0: #Just loop for every never stopping the monitoring of the temperatures
		now = datetime.datetime.now()
		if str(now)[0:10] != date_str: #checks if the day has changed (i.e.) at midnight,if it is a new day start a new file
			f.close() #close the old file
			date_str = str(now)[0:10]
			file_prefix =  "./Temps/" + date_str
			file_suffix = ''
			file_prefix2 =  "./Voltage_Current/" + date_str


			f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a new file to write the temperatures to
			g = open(file_prefix2 + file_suffix +'_VI.txt' ,'w')

		# Current time
		new_time = time.time()-start

		# Poll the new data
		new_temps = get_temps()
		_, new_volt, new_curr = read_power_supplies()
		power_labels = MonitorPlot.get_volt_labels()

		# Update the plot
		monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0])

		# Get shorthands for the data
		t = new_time
		y = monitor_plot.T_data
		volt_y = monitor_plot.V_data
		curr_y = monitor_plot.A_data
		temps = new_temps
		volt = new_volt
		curr = new_curr

		# should be able to load all of them at once
		lk218_T1 = y[-1,0]
		lk218_T2 = y[-1,1]
		lk218_T3 = y[-1,2]
		lk218_T4 = y[-1,3]
		lk218_T5 = y[-1,4]
		lk218_T6 = y[-1,5]
		lk218_T8 = y[-1,6]
		lk224_TC2 = y[-1,7]
		lk224_TC3 = y[-1,8]
		lk224_TC4 = y[-1,9]
		lk224_TC5 = y[-1,10]
		lk224_TD1 = y[-1,11]
		lk224_TD2 = y[-1,12]
		lk224_TD3 = y[-1,13]
		lk224_TD4 = y[-1,14]
		lk224_TD5 = y[-1,15]
		lk224_A = y[-1,16]
		lk224_B = y[-1,17]
		lr750_a_temp = y[-1,18]

		#fridge cycle crap starts here
		#the way I am doing it is a bit weird we are just continuously looping
		#and executing certain fridge steps if the time is appropriate
		#rather than just do things step by step.
		#step 1 is open (heat) the ADR switch

		# ADR heat switch want to leave open so that the 1K head can cool the ADR
		# but turn off before cycle ADR
		# doesn't cool well if the 4K-1K switch is not on and the film burner is hot
		if adrOn == 'Y':
			if t>10*60: #70,800
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.7')#3.5 #Afyhrie changed from 1.75 to 1.5 on June 28 2017
				#to make sure the ADR switch doesn't heat above 17 K

		#Heat up the 4He pump
		if t>0*60 and t<50*60:
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
		if t>30*60 and t<t_cool_He3_pump*60:
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
		if t>50*60:
			if lk224_TC4<29.:
				if temps[7]>40.: #4He pump
					ag47b.write('INST:SEL OUT1')
					ag47b.write('Volt 2')#was 4 3V gets me to 21.3K 4K plate still heated to 8.5K
				elif temps[7]>20:
					ag47b.write('INST:SEL OUT1')
					ag47b.write('Volt 2.2')#was 4 3V gets me to 21.3K 4K plate still heated to 8.5K
				else:
					ag47b.write('INST:SEL OUT1')
					ag47b.write('Volt 3.0')				
			if lk224_TC4>30.: #just in case 2v gets to 14.35
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 0')
		elif t<-20*60: #this ensures it turns of the switches 15min before cycling
			pass#do nothing 
		else:
			ag47b.write('INST:SEL OUT1')
			ag47b.write('Volt 0')

		#close (heat) the He3 switch turn on when He3 pump is turned off leave on forever
		if t>t_cool_He3_pump*60:
			if lk224_TC5<30.:
				if temps[8]>20.:
					ag47b.write('INST:SEL OUT2')
					ag47b.write('Volt 1.9')#3.6 3V got me 20.4K
				else:
					ag47b.write('INST:SEL OUT2')
					ag47b.write('Volt 3')#3.6 3V got me 20.4K
			if lk224_TC5>35.: #just in case
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 0')
		elif t<-20*60:
			pass #do nothing
		else:
			ag47b.write('INST:SEL OUT2')
			ag47b.write('Volt 0')

		#monitor when the fridge cycle is complete
		if t>(t_cool_He3_pump+20.)*60:
			if lk224_A<0.4:
				print("fridge cycle complete")
				finished =1

		seconds = int(t)
		minutes = int(t/60)
		if seconds >= 60:
			seconds = int(t-(60*minutes))
		#print('Cycle duration: ',minutes, ':', seconds)

		#Alarm function
		DisableTextAlarm = False # This can be flipped to disable the text message alerts if testing directly on tycho
		if Alarm != 0: #if the alarm is turned on proceed
			Alarm_test = y[419,:]*Alarm_on #0 if not on otherwise actual temperature
			if (Alarm_test>(Alarm_value +.001)).any() == True: #have any of the alarm values been reached
				print("Alarm Alarm")
				if Alarm == 1 and not DisableTextAlarm: # we only want it to send us texts once not over and over again
					print("first occurrence")
					fromaddr = 'SubmmLab@gmail.com'
					toaddrs  = '3145741711@txt.att.net' #jordan
					msg = 'The temperature alarm was triggered'
					username = 'SubmmLab@gmail.com'
					password = 'ccatfourier'
					server = smtplib.SMTP_SSL('smtp.gmail.com:465')
					server.ehlo()
					#server.starttls()
					server.login(username,password)
					server.sendmail(fromaddr, toaddrs, msg) #send a text
					#toaddrs  = '3038192582@tmomail.net'#jason
					#server.sendmail(fromaddr, toaddrs, msg)
					#toaddrs  = '5308487272@pm.sprint.com'#addi
					#server.sendmail(fromaddr, toaddrs, msg)
					server.quit()
				Alarm = 2 #Alarm on but already triggered


		if i == 0: #if it is the first time writing to file put in a header
			# not sure this header is up to date also need to add header if a new day has started
			print('#Human readable time. Time (s) since start. Lakeshore temperature sensor 218 T1,2,3,4,5,6,8 and 224 C2,C3,C4,C5,D1,D2,D3,D4,D5,A,B, LR750',file=f)
			print('#Human readable time. Time (s) since start. V @ ag47t. A @ ag47t. V @ ag47b. A @ ag47b. V @ ag49. A @ ag49.', file=g)

		# write temps to file
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(y[-1,0])+' '+ str(y[-1,1])+' '+ str(y[-1,2])+' '+ str(y[-1,3])+' '+ str(y[-1,4])+' '+ str(y[-1,5])+' '+ str(y[-1,6])+' '+ str(y[-1,7])+' '+ str(y[-1,8])+' '+ str(y[-1,9])+' '+ str(y[-1,10])+' '+ str(y[-1,11])+' '+ str(y[-1,12])+' '+ str(y[-1,13])+' '+ str(y[-1,14])+' '+ str(y[-1,15])+' '+ str(y[-1,16])+' '+ str(y[-1,17])+' '+str(y[-1,18]), file = f) #print the temperature and some nonsense numbers to the file
		print(str(np.round(t,3)).strip()+' ',end = '')
		for k in plots:
			# write to command prompt
			print(str(y[-1, k])+" ",end = '')
		print('')#print newline



		#print the current and voltage to the file
		volt_str = ''
		for k in range(0, len(volt)):
			volt_str = volt_str + str(volt_y[-1,k])
			if k!=len(volt)-1:
				volt_str = volt_str + ","
			#print(str(volt_y[419, k])+'V '+str(curr_y[419, k])+'I ', file = g)

			# write to command prompt
			#print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(volt_y[419, k])+' '+ str(curr_y[419, k]))
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ volt_str,file = g)

		i = i + 1 #icrement the counter

		# Wait the plot
		monitor_plot.wait()

	f.close()
	g.close()
	if adrOn == 'Y':
		os.system("python ADR.py")
		#import ADR #execfile("ADR.py",globals())#need globals() or else temp fails
	else:
		execfile("monitor_all.py")

except KeyboardInterrupt:
	pass

print("Human interupted the fridge cycle")
