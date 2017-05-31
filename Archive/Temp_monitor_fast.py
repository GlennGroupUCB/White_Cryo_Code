from __future__ import print_function
import numpy as np
import visa
import matplotlib
import time
import datetime
import os
import smtplib
from scipy import interpolate
from functions import read_power_supplies, get_temps, get_press, plot_and_write

#Program to monitor the temp. voltage, current and pressure roughly every second and alert. Also calls functions to write and plot data every 60 seconds.
#written by Tim, stolen from Jordan in March 2017

#Change log
#03/15/17 - Tim - Got rid of plotting from original, changed timeout of get_press() to 0.1, now updates every 0.71 sec.

#To Do 
#write data to file in 60 sec. increments
#call function to take data from file and plot


RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#202 ADR sensor look up table
#RX202_lookup = np.loadtxt('RX-102A Mean Curve.tbl') #102 300mK/ 1K sensors
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False) # interpolates the temperature when in between lookup table values
#test = np.float(RX202_interp(4000))
#RX202_temps = RX202_interp(-linear_bridge*1000)

# turn on alarm on for certain values
#                     4K P.T--50K HTS--50K P.T.--50K plate--ADR rad shield'--4He pump--3He pump--4He switch--3He switch--ADR switch--4K-1K switch--4K plate--3He head--4He head--4K HTS--ADR--Head ADR switch
Alarm_on = np.array((    0,     1,       0,         0,           0,             0,       0,        0,           0,          0,         0,             1,         0,       0,       1,    0,      0         ))
Alarm_value =np.array((  0,     60.,   333  0,         0,           0,             0,       0,        0,           0,          0,         0,             5.,        0,       0,       8.,   0,      0         ))

#sleep_interval = 10. #seconds change back
Alarm = 0 # 0 for off 1 for on

now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
file_suffix = ''
file_prefix2 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Voltage_Current/" + date_str
file_prefix3 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Pressure/" + date_str


#create a resourcemanager and see what instruments the computer can talk to
#path = os.path.normpath("C:/Program Files/IVI Foundation/VISA/Win64/Lib_x64/msc/visa64.lib")
rm = visa.ResourceManager()
print, rm.list_resources()

#form connections to the two lakeshore temperature sensors available
lk224 = rm.open_resource('GPIB0::12::INSTR') #lakeshore 224
lk218 = rm.open_resource('GPIB0::2::INSTR') #lakeshore 218
lr750 = rm.open_resource('GPIB0::4::INSTR') #linear bridge

#double check that you've connected to the lakeshore temperature sensors by asking them their names
print(lk218.query('*IDN?'))
print(lk224.query('*IDN?'))

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
		
		#grab pressure 
		press = get_press()
		press_y[419,:]=press
		
		#grab temperatures and store them to the temperature array	
		temps = get_temps()
		y[419,:] = temps
		
		#print(lr750_a)
		if i == 0: # there is some weirdness where the first call returns an empty string
			lr750_a_temp = -1
		if i != 0:
			try: #every once in a while this fails
				lr750_a_num = np.float(lr750_a[0:8]) #convert resitance string to float
				print(lr750_a_num)
				y[419,15] = lr750_a_temp = RX202_interp(-lr750_a_num*1000) # convert restance value to temperature
			except:
				y[419,15] = lr750_a_temp = -1. #if we get a bad string just return -1
		
	
		#grab voltages and current from power supplies
		power_labels, volt, curr = read_power_supplies()
		volt_y[419,:]= volt
		curr_y[419,:]= curr	
	
		#Alarm function
		if Alarm != 0: #if the alarm is turned on proceed
			Alarm_test = y*Alarm_on #0 if not on otherwise actual temperature
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
		if time = 60:
			plot_and_write(i, y, press_y, curr_y, volt_y, volt, power_labels, )
		#need to change this
		
				
				
		
except KeyboardInterrupt: #if you press ctrl c quit
    pass

f.close() #close the file

print("Temperature monitoring disabled")
