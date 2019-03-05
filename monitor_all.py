from __future__ import print_function
import numpy as np
import visa
import matplotlib
#matplotlib.use('qt4agg')#need for continuously updating plot
matplotlib.use('TkAgg') #seems to be more responsive and less glitchy than gt4agg
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib
from scipy import interpolate
from functions import read_power_supplies, get_temps, get_press, initialize
import matplotlib.gridspec as gridspec
import sys
import power_supply as ps
from monitor_plot import MonitorPlot
from ADRinterrupt import InterruptClient

#Program to monitor the temperatures of the cyrostat
#written by Jordan at some date lost in time. 

#CHANGE LOG
#12/9/16 - Jordan - Added reading and ploting of the voltage and currents of the power supplies.
#01/22/17 - Jordan - Added a bunch of comment to clarify the code
#03/10/17 - Tim - Added integration with functions.py. Now can read temp., pressure, Volt, and Curr
#03/13/17 - Tim - Plots pressure and creates text files. Added headers to Volt and Press
#05/11/17 - Tim - Changed plots to reflect new temp sensors, fixed print to file for temps, set alarm to 0
#02/??/18 - Jordan - cleaned up printing to screen
#03/09/18 - Jordan - incorporated cooldown.py as a mode in this code
#05/31/18 - Sean - changed the plotting code to use the new MonitorPlot class in monitor_plot.py
#8/30/18 - Sean added the InterruptClient code to allow the temperature to be changed from this program

#TO DO 
#the power supplies need to call power_supply.py

if __name__=='__main__':
	if len(sys.argv) < 2:
		print('Starting in Monitoring mode')
		mode = 'monitor'
	else:
		mode = sys.argv[1]
		if mode == "cooldown":
			print("Starting in cooldown mode")
		elif mode == "monitor":
			print("Starting in monitor mode")
		else:
			print("please choose mode that exists i.e. monitor or cooldown")
			sys.exit()
		
		
Cold_enough = 0
def cooldown(temps):
	#print(temps[9],temps[10])
	if temps[9] < 8.5 and temps[10] <8.5: #are the switches cold enough
		global Cold_enough
		Cold_enough = 1
		#print("The cyostat is cold enough to turn on the pumps.")

	#Heat up the 4He pump
	if Cold_enough == 1 and temps[15]<12.: # if the switches have coold and just in case if the 4K plate gets to hot
		#print("test")
		if temps[7]<45.:
			ps.change_voltage('He4 pump',25)
		if temps[7]>45.:
			ps.change_voltage('He4 pump',25)
		if temps[7]>50.:	
			ps.change_voltage('He4 pump',0)
	else:
		ps.change_voltage('He4 pump',0)
		
	#Heat up the He3 
	if Cold_enough == 1 and temps[15]<12.:
		if temps[8]<45.:
			ps.change_voltage('He3 pump',15)
		if temps[8]>45.:
			ps.change_voltage('He3 pump',5)
		if temps[8]>50.:
			ps.change_voltage('He3 pump',0)
	else:
		ps.change_voltage('He3 pump',0)
		
	# turn on the ADR switch when it gets to cold to conduct	
	if temps[12]<30.:
		if 0.1 <temps[18]<30:
			ps.change_voltage('ADR switch',1.75)
		else:
			ps.change_voltage('ADR switch',2.75)
	if temps[12]>30.: #temp should drop slowly
		ps.change_voltage('ADR switch',0)
	if temps[12]>35.: #just in case
		ps.change_voltage('ADR switch',0)
	

RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#202 ADR sensor look up table
#RX202_lookup = np.loadtxt('RX-102A Mean Curve.tbl') #102 300mK/ 1K sensors
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False) # interpolates the temperature when in between lookup table values
#test = np.float(RX202_interp(4000))
#RX202_temps = RX202_interp(-linear_bridge*1000)

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
head_count = 0
Alarm = 0 # 0 for off 1 for on

now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
file_prefix =  "./Temps/" + date_str
file_suffix = ''
file_prefix2 =  "./Voltage_Current/" + date_str
file_suffix2 = ''
file_prefix3 =  "./Pressure/" + date_str
file_suffix3 = ''

# Create the monitor plot class and show it
monitor_plot = MonitorPlot(sleep_interval, 420)
monitor_plot.show()

start = time.time() #define a start time
if os.path.isfile(file_prefix + '_temps.txt') == True: #check if there is already a file with the prefix we are trying to use
	#If a file already exists add a suffix to the end that consist of the time it was created so it can be distinguished from the original file
	file_suffix = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16] 
f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a file to write the temperatures to

if os.path.isfile(file_prefix2 + '_VI.txt') == True: 
	file_suffix2 = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16] 
g = open(file_prefix2 + file_suffix2 +'_VI.txt' ,'w') 

if os.path.isfile(file_prefix3 + '_press.txt') == True: 
	file_suffix3 = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16] 
p = open(file_prefix3 + file_suffix3 +'_press.txt' ,'w') 

i = 0 #initialize a counter
try: #allows you to kill the loop with ctrl c
	while True: #Just loop for every never stopping the monitoring of the temperatures
		now = datetime.datetime.now()
		if str(now)[0:10] != date_str: #checks if the day has changed (i.e.) at midnight,if it is a new day start a new file
			f.close() #close the old file
			date_str = str(now)[0:10]
			file_prefix =  "./Temps/" + date_str
			file_suffix = ''
			file_prefix2 =  "./Voltage_Current/" + date_str
			file_prefix3 = "./Pressure/" + date_str
			
			f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a new file to write the temperatures to
			g = open(file_prefix2 + file_suffix +'_VI.txt' ,'w') 
			p = open(file_prefix3 + file_suffix + '_press.txt', 'w')
			
		# Current time
		new_time = time.time()-start

		# Poll the new data
		new_temps = get_temps()
		new_press = get_press()
		_, new_volt, new_curr = read_power_supplies()
		power_labels = MonitorPlot.get_volt_labels()

		# Update the plot
		monitor_plot.update(new_time, new_temps, new_volt, new_curr, new_press)
		
		# Get shorthands for the data
		t = new_time
		y = monitor_plot.T_data
		volt_y = monitor_plot.V_data
		curr_y = monitor_plot.A_data
		press_y = monitor_plot.P_data
		press = new_press
		temps = new_temps
		volt = new_volt
		curr = new_curr

		#Alarm function
		DisableTextAlarm = False # This can be flipped to disable the text message alerts if testing directly on tycho
		if Alarm != 0: #if the alarm is turned on proceed
			Alarm_test = y[-1,:]*Alarm_on #0 if not on otherwise actual temperature
			if (Alarm_test>(Alarm_value +.001)).any() == True: #have any of the alarm values been reached
				print("Alarm Alarm")
				if Alarm == 1 and not DisableTextAlarm: # we only want it to send us texts once not over and over again
					print("first occurance")
					fromaddr = 'SubmmLab@gmail.com'
					toaddrs  = '3145741711@txt.att.net'
					msg = 'The temperature alarm was triggered'
					username = 'SubmmLab@gmail.com'
					password = 'ccatfourier'
					server = smtplib.SMTP_SSL('smtp.gmail.com:465')
					server.ehlo()
					#server.starttls()
					server.login(username,password)
					server.sendmail(fromaddr, toaddrs, msg) #send a text
					toaddrs  = '3038192582@tmomail.net'
					server.sendmail(fromaddr, toaddrs, msg)
					toaddrs  = '5308487272@pm.sprint.com'
					server.sendmail(fromaddr, toaddrs, msg)
					server.quit()	
				Alarm = 2 #Alarm on but already triggered
				
				
		if i == 0: #if it is the first time writing to file put in a header
			# not sure this header is up to date also need to add header if a new day has started
			print('#Human readable time. Time (s) since start. Lakeshore temperature sensor 218 T1,2,3,4,5,6,8 and 224 C2,C3,C4,C5,D1,D2,D3,D4,D5,A,B, LR750',file=f)
			print('#Human readable time. Time (s) since start. Pressure (torr).', file = p)
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
			
			
		
		
		# write press to file
		 
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(press_y[-1,0])+' ', file = p) #print the temperature and some nonsense numbers to the file
		# write to command prompt
		#print( str(np.round(t,3)).strip()+' '+ str(press_y[419, 0]))	
		
		#print the current and voltage to the file
		volt_str = ''
		for k in range(0, len(volt)): 
			volt_str = volt_str + str(volt_y[-1,k])
			if k!=len(volt)-1:
				volt_str = volt_str + ","
			#print(str(volt_y[419, k])+'V '+str(curr_y[419, k])+'I ', file = g) 
			
			# write to command prompt
			#print(str(np.round(t,3)).strip()+' '+ str(volt_y[419, k])+' '+ str(curr_y[419, k]),end = '')
		#print("")#print newline
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ volt_str,file = g)
		#time.sleep(sleep_interval)#sleep for 60 second

		# Wait the plot
		monitor_plot.wait()
		
		i = i + 1 #increment the counter
		
		if mode == 'cooldown':
			cooldown(temps)
			
				
		
except KeyboardInterrupt: #if you press ctrl c quit
	pass

f.close() #close the file

print("Monitoring disabled")


