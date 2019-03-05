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
import power_supply as ps

#########################################################
#      Program to cycle the Chase fridge                #
#########################################################

#CHANGE LOG
#8/7/17 - Added menu to prompt user for start time and adr switch
#1/23/18 -Jordan putting finished back in for the while loop so that it can auto trigger ADR.py when it is done
#1/25/18 - Jordan made it so instead of sleeping until starting the fridge cycle it just starts at t<0 and
# 			doesn't do anything until t=0
#5/31/18 - Sean - Integrated the new MonitorPlot class into this script
#2/14/18 - Jordan cleaned up the code. removed old lines that were not nessacary and changed power supply calls

finished = 0
head_count = 0

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

#initialize plot resources from functions
lines, colors, labels, plots = initialize()

# turn on alarm on for certain values
Alarm_on = np.array((0,#4K P.T.   0            
	0,#	4K HTS           1
	0,#	50K HTS          2
	0,#	Black Body       3
	0,#	50K P.T.         4
	0,#	50K Plate        5
	0,#	ADR Shield       6
	0,#	4He Pump         7
	0,#	3He Pump         8
	0,#	4He Switch       9
	0,#	3He Switch       10
	0,#	300 mK Shield    11
	0,#	ADR Switch       12
	0,#	4-1K Switch      13
	0,#	1K Shield        14   
	0,#	4K Plate         15 
	0,#	3He Head         16
	0,#	4He Head         17
	0))#ADR              18
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

		
		# fridge cycle starts here
		# the way I am doing it is a bit weird we are just continuously looping
		# and executing certain fridge steps if the time is appropriate
		# rather than just do things step by step.
		# step 1 is open (heat) the ADR switch

		# ADR heat switch want to leave open so that the 1K head can cool the ADR
		# doesn't cool well if the 4K-1K switch is not on and the film burner is hot
		if adrOn == 'Y':
			if t>10*60: #70,800
				ps.change_voltage('ADR switch',1.75)

		#Heat up the 4He pump
		if t>0*60 and t<50*60:
			if temps[7]<45.: #4He pump
				ps.change_voltage('He4 pump',25)
			if temps[7]>45.:
				ps.change_voltage('He4 pump',15)
			if temps[7]>50.:
				ps.change_voltage('He4 pump',0)
		else:
			ps.change_voltage('He4 pump',0) #watch out

		#Heat up the He3 pump turn off 50mins after He4 pump is turned off
		if t>30*60 and t<t_cool_He3_pump*60:
			if temps[8]<45.:#3He pump
				ps.change_voltage('He3 pump',15)
			if temps[8]>45.:
				ps.change_voltage('He3 pump',5)
			if temps[8]>50.:
				ps.change_voltage('He3 pump',0)
		else:
			ps.change_voltage('He3 pump',0)

		#close (heat) the He4 switch turn on when He4 pump is turned off leave on forever
		if t>50*60:
			if temps[9]<29.: #4He switch
				if temps[7]>40.: #4He pump
					ps.change_voltage('He4 switch',2)
				elif temps[7]>20:
					ps.change_voltage('He4 switch',2.2)
				else:
					ps.change_voltage('He4 switch',3.0)				
			if temps[9]>30.: #just in case 2v gets to 14.35
				ps.change_voltage('He4 switch',0)
		elif t<-20*60: #this ensures it turns of the switches 15min before cycling
			pass#do nothing 
		else:
			ps.change_voltage('He4 switch',0)

		#close (heat) the He3 switch turn on when He3 pump is turned off leave on forever
		if t>t_cool_He3_pump*60:
			if temps[10]<30.:
				if temps[8]>20.:
					ps.change_voltage('He3 switch',1.9)
				else:
					ps.change_voltage('He3 switch',3)
			if temps[10]>35.: #just in case
				ps.change_voltage('He3 switch',0)
		elif t<-20*60:
			pass #do nothing
		else:
			ps.change_voltage('He3 switch',0)

		#monitor when the fridge cycle is complete
		if t>(t_cool_He3_pump+20.)*60:
			if temps[16]<0.4:
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
		if head_count == 0:
			head_count = 10
			print("")
			print(str(now)[0:19]+" ",end='')
			for k in plots:
				print(labels[k][0:6]+" ",end = "")
			print("")
		head_count = head_count-1
		print(str(now)[0:19]+" ",end='')
		for k in plots: 
			# write to command prompt
			#print(" %2.2f" %y[419,k],end = '')
			print(str(y[419,k]+.00001)[0:6]+" ",end = '')
			#print(str(np.round(t,3)).strip()+' '+ str(y[419, k]),end = '')
		print('')#print new line



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
		#os.system("python ADR.py")
		print("turn auto statrt back on")
		#import ADR #execfile("ADR.py",globals())#need globals() or else temp fails
	else:
		execfile("monitor_all.py")

except KeyboardInterrupt:
	pass

print("Human interupted the fridge cycle")
