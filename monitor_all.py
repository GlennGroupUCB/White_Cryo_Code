from __future__ import print_function
import numpy as np
import visa
import matplotlib
matplotlib.use('qt4agg')#need for continuously updating plot
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib
from scipy import interpolate
from functions import read_power_supplies, get_temps, get_press, initialize
import matplotlib.gridspec as gridspec

#Program to monitor the temperatures of the cyrostat
#written by Jordan at some date lost in time. 

#CHANGE LOG
#12/9/16 - Jordan - Added reading and ploting of the voltage and currents of the power supplies.
#01/22/17 - Jordan - Added a bunch of comment to clarify the code
#03/10/17 - Tim - Added integration with functions.py. Now can read temp., pressure, Volt, and Curr
#03/13/17 - Tim - Plots pressure and creates text files. Added headers to Volt and Press
#05/11/17 - Tim - Changed plots to reflect new temp sensors, fixed print to file for temps, set alarm to 0

#TO DO 

RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#202 ADR sensor look up table
#RX202_lookup = np.loadtxt('RX-102A Mean Curve.tbl') #102 300mK/ 1K sensors
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False) # interpolates the temperature when in between lookup table values
#test = np.float(RX202_interp(4000))
#RX202_temps = RX202_interp(-linear_bridge*1000)

lines, colors, labels, plots = initialize()

# turn on alarm on for certain values
#                     4K P.T--4K HTS--50K HTS--Black Body--50K P.T.--50K Plate--ADR Shield--4He Pump--3He Pump--4He Switch--3 He Switch--300 mK Shield--ADK Switch--4-1K Switch--1K Shield--3He Head--4He Head--ADR--
Alarm_on = np.array((  0,     0,       0,         0,           0,             0,       0,        0,           0,          0,         0,             0,        0,      0,       0,    0,      0, 	0))
Alarm_value =np.array((0,     0,       0,         0,           0,             0,       0,        0,           0,          0,         0,             0,        0,      0,       0,    0,      0, 	0))

sleep_interval = 10. #seconds change back
Alarm = 0 # 0 for off 1 for on

now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
file_suffix = ''
file_prefix2 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Voltage_Current/" + date_str
file_suffix2 = ''
file_prefix3 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Pressure/" + date_str
file_suffix3 = ''

plt.figure(1,figsize = (21,11))
ax = plt.gca() #need for changing legend labels
x = np.arange(-420,0)*1. # initalize the x axis i.e. time going 420 mins into the past
#print(x[0],x[419])
y = np.ones((420,19))*-1 #initalize array to hold temperautere
volt_y = np.zeros((420,6)) #initialize array to hold voltages
curr_y = np.zeros((420,6)) #initialize array to hold currents
press_y = np.zeros((420,1))

plt.title("Thermometry")
plt.xlabel("time (mins)")
plt.ylabel("Temperature (K)")
plt.ion() #need for constantly updating plot
gs = gridspec.GridSpec(4,4)#allows for custom subplot layout
plt.show()

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
			file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
			file_suffix = ''
			file_prefix2 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Voltage_Current/" + date_str
			file_prefix3 = "C:/Users/tycho/Desktop/White_Cryo_Code/Pressure/" + date_str
			
			f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a new file to write the temperatures to
			g = open(file_prefix2 + file_suffix +'_VI.txt' ,'w') 
			p = open(file_prefix3 + file_suffix + '_press.txt', 'w')
			
			
		t = time.time()-start #current time
		x = np.roll(x,-1) #shift the time array by 1 interval
		x[419] = t/60. #record current time to last position of time array
		y = np.roll(y,-1,axis = 0) # shift temperature array by 1 interval
		volt_y = np.roll(volt_y,-1,axis = 0) #shift voltage array by 1 interval
		curr_y = np.roll(curr_y,-1,axis = 0) #shift current array by 1 interval
		press_y = np.roll(press_y,-1,axis = 0) #shift pressure array by 1 interval

		#grab pressure and store in pressure array
		press = get_press()
		press_y[419,:]=press
		
		#grab temperatures and store them to the temperature array	
		temps = get_temps()
		y[419,:] = temps
		
		
		k = 0 #intiialize a counter
		
		plt.subplot(gs[0:2,:]) #create top subplot 
		for j in plots: #plot all of the temperatures with appropriate labels
			#print(y[419,j])
			plt.semilogy(x,y[:,j],color = colors[np.mod(j,7)],linestyle = lines[j/7],linewidth = 2, label = labels[k]+" " +str(y[419,j])[0:5]+"K")
			if i != 0:
				legend.get_texts()[k].set_text(labels[k]+" " +str(y[419,j])[0:5]+"K") #if it is not the first time ploting rewrite the legend with the new temps
			k = k+1
			
		if i == 0:	#if it is the first time ploting generate the legend				
			legend = plt.legend(ncol = 2,loc =2)
		plt.xlim(x[0],x[419])
		plt.ylim(0.1,300)
		
		#grab voltages and current from power supplies
		power_labels, volt, curr = read_power_supplies()
		volt_y[419,:]= volt
		curr_y[419,:]= curr
		
			
		# plot the power levels	
		plt.subplot(gs[2,:])
		k = 0
		for j in range(0,len(volt)):
			plt.plot(x,volt_y[:,j],color = colors[np.mod(j,7)],linestyle = lines[j/7],linewidth = 2, label = power_labels[j]+ " " +str(volt_y[419,j])[0:4]+"V " + str(curr_y[419,j])[0:6]+"A")
			if i != 0:
				legend_power.get_texts()[k].set_text(power_labels[j]+" " +str(volt_y[419,j])[0:4]+"V "+ str(curr_y[419,j])[0:6]+"A")#if it is not the first time ploting rewrite the legend with the new temps
			k = k+1
		if i ==0:
			legend_power= plt.legend(ncol = 2,loc = 2)	 #If it is the first time plotting generate the legend	
		plt.xlim(x[0],x[419])
		plt.ylim(0,30)
		
		
		#plot pressure
		try:
			plt.subplot(gs[3,:])
			plt.semilogy(x,press_y, color = 'b', linestyle = '-', linewidth = 2, label = 'Pressure ' + str(press_y[419,0]) + ' mbar')
			if i!=0:
				legend_press.get_texts()[0].set_text('Pressure ' + str(press_y[419,0]) + ' mbar')
			if i==0:
				legend_press= plt.legend(ncol = 1, loc = 2)
			plt.xlim(x[0],x[419])
			plt.ylim((1*10**-6),1)
			
			plt.draw() #update the plot
		except:
			print("Not plotting pressure")
			

		#Alarm function
		if Alarm != 0: #if the alarm is turned on proceed
			Alarm_test = y[419,:]*Alarm_on #0 if not on otherwise actual temperature
			if (Alarm_test>(Alarm_value +.001)).any() == True: #have any of the alarm values been reached
				print("Alarm Alarm")
				if Alarm == 1: # we only want it to send us texts once not over and over again
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
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(y[419,0])+' '+ str(y[419,1])+' '+ str(y[419,2])+' '+ str(y[419,3])+' '+ str(y[419,4])+' '+ str(y[419,5])+' '+ str(y[419,6])+' '+ str(y[419,7])+' '+ str(y[419,8])+' '+ str(y[419,9])+' '+ str(y[419,10])+' '+ str(y[419,11])+' '+ str(y[419,12])+' '+ str(y[419,13])+' '+ str(y[419,14])+' '+ str(y[419,15])+' '+ str(y[419,16])+' '+ str(y[419,17])+' '+str(y[419,18]), file = f) #print the temperature and some nonsense numbers to the file
		for k in range(0,len(temps)): 
			# write to command prompt
			print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(y[419, k]))
			
			
		
		
		# write press to file
		 
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(press_y[419,0])+' ', file = p) #print the temperature and some nonsense numbers to the file
		# write to command prompt
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(press_y[419, 0]))	
		
		#print the current and voltage to the file
		volt_str = ''
		for k in range(0, len(volt)): 
			volt_str = volt_str + str(volt_y[419,k])
			if k!=len(volt)-1:
				volt_str = volt_str + ","
			#print(str(volt_y[419, k])+'V '+str(curr_y[419, k])+'I ', file = g) 
			
			# write to command prompt
			print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(volt_y[419, k])+' '+ str(curr_y[419, k]))
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ volt_str,file = g)
		#time.sleep(sleep_interval)#sleep for 60 second
		plt.pause(sleep_interval) # pause for sleep interval before looping again
		
		i = i + 1 #icrement the counter
				
		
except KeyboardInterrupt: #if you press ctrl c quit
    pass

f.close() #close the file

print("Monitoring disabled")
