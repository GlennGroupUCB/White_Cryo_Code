from __future__ import print_function
import sys
import visa
import serial
import time
import os
import datetime
if "get_temps" not in sys.modules: #already imported when called by fridge cycle?
	from functions import get_temps, initialize, read_power_supplies
import csv
import threading
from Tkinter import *
import argparse
import power_supply as ps
from simple_pid import PID
from ADRinterrupt import InterruptServer
from monitor_plot import MonitorPlot
import numpy as np

#Change log
#1/23/18 -Jordan added default fill and set temp to .1K and added an autostart functionality
#1/25/18 -Jordan updated print to be future print and cleaned up print dispay so that I can excute ADR.py from fridge_cycle.py
#changed the ramp down to always have a target of zero so that it doesn't get stuck if it reaches target
#before it hits a temperature condition with a zero target
#3/12/18 -Jordan changed ramp down rates to be negative so resistance in calculted correctly
# also also added time.sleep(5) whenever you change dIdt so that it has time to settle
# before measuring the resistance of the magnet
#8/30/18 - Sean added the InterruptServer code to allow the temperature to be changed from other programs
#9/24/18 - Sean added the init_count() function
#2/20/2019 - Jodan - Major rework to to add in the fridge cycle so that the 4K can sink the heat of magnitization
#            attempted to make the whole code more linear and easier to understand see main for the action
#			 also added in plotting so that you can see what the hell is going on 
#2/21/2019 - Jordan - added in PID loop for temperature control

'''
READ ME:
This script is written to be run the fridge cycle and ADR simultaneously maximizing the 4He head hold time.
1) Set the desired temperature you want the ADR to run at. (This can be changed while running the code.)
2) Hit Start to begin the script. 
3) The PAUSE function, shold just pause the pid loop

   NOTES:
*   To safegaurd the magnet, the code has a number of try statements whenever there is a serial command that could possibly return an error.
	If one of these try statements fail, it will call the stop function which will ramp down to zero current at 0.5 A/min and trigger the alarm.
*	Set delay takes input in form of 'hours:minutes' i.e 10:30 will run in 10hrs and 30min from pushing start

Code is run by moving from state to state as indicated by count
count = -3 Turn off/make sure 4He and 3He switches are off
count = -2 Heat the 4He pump/ Turn on ADR switch
count = -1 Heat the 3HE pump
count = 0 => saftey check before ramping
count = 1 => Ramp up to 10 A
count = 2 => Sink 4He pump
count = 3 => Sink 3He pump
count = 4 => Turn off ADR switch
count = 5 => ramp down/maintain specified temperature
count = 6 => Cuntinue plotting if current is exhasted or ermergency has been triggered
'''

'''
To Do list 
- Tune the PID parameters
- Fix Pause/Resume button so it pause/resumes the PID loop/ramping of magnet current
-    need to test
- Test failsafes
- Add in an timeout for talking to the AMI and an except each time to make sure the AMI is reponding
'''
auto_start = 0 #0 don't auto start 1 do auto start
sleep_interval = 3 #time to wait in between plotting intervals
Alarm = 0
temp = 0
L = 16 #magnet Inductance
running = True
first = True
dont_stop = True #cant stop... A boolean to break out of count = 5 and ramp to zero


# Allows count to be set by a command line argument of the form `--count #` or `-c #`
def init_count():
	argp = argparse.ArgumentParser()
	argp.add_argument('-c', '--count', dest='count', type=int, nargs=1, default=0)
	try:
		result = argp.parse_args()
	except Exception: 
		print('Using count=0')
		return 0
	return result.count
	
#intialize the count
count = init_count() # Allows count to be set with a command line argument
try:
	count = count[0]
except:
	count = -3	
print("the count is ",count)
if count == -1:#If starting with 4He head already hot
	sleep_time = -30*60 #since the first part of cycle is time based

	
t=0 #is this used?
sleep_time = 0 #for delay
dIdt = 0
tk_app = None
	
# create (but dont open) the interrupt server
interrupt_server = InterruptServer(password='')

#connect to AMI controller
ami = serial.Serial('COM6', 115200, rtscts=1)
ami.write('SYST:LOC\n')

#The Model 430 Programmer uses the following parameters related to the
#RS-232 interface:
# Baud Rate: 115200
# Parity: No Parity
# Data Bits: 8 Data Bits
# Number of Start Bits: 1 bit
# Number of Stop Bits: 1 bit
# Flow Control: Hardware (RTS/CTS)

ami.write('RAMP:RATE:UNITS?\n')
unit = ami.readline()
unit = int(unit)
if unit == 0:
	print('Ramp rate is in seconds')
	print("please change the unists")
	sys.exit()
if unit == 1:
	print('Ramp rate is in minutes')
#Sets voltage limit to 0.25V, may need to be higher depending on ramp rate.
ami.write('CONF:VOLT:LIM 0.25\n')
ami.write('VOLT:LIM?\n')
voltLim = ami.readline()
print('Voltage limit: ')
print(voltLim)
#Returns the target current setting in amperes.
ami.write('CURR:TARG?\n')
targ = ami.readline()
print('Target: ')
print(targ)
	
#intialize a pid for temperature control
use_pid = False
pid = PID(0.01,0.0,0.0,output_limits = (-0.25,0.1)) #PID loop for temperature control
pid.sample_time = 10#

#intialize the time to start
start_time = time.time()+sleep_time

#Initialize writing to file
now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
#file_prefix =  "/home/timotheous/White_Cryo_Code/ADR/" + date_str
file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/ADR/" + date_str
file_suffix = ''

if os.path.isfile(file_prefix + '_ami_data.csv') == True: #check if there is already a file with the prefix we are trying to use
	#If a file already exists add a suffix to the end that consist of the time it was created so it can be distinguished from the original file
	file_suffix = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
csvfile = open(file_prefix + file_suffix +'_ami_data.csv' ,'wb') #open a file to write the data to
writer = csv.writer(csvfile)

def main():
	global start_time
	global count
	global dIdt
	while True: #Main is always looping
	
		new_time = time.time()-start_time #current time
		new_temps = get_temps()
		_, new_volt, new_curr = read_power_supplies()
		#monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0])
		dIdt,volt,targ,curr,Z = get_ami_data(ami)
		
		if count == -3: #make sure the 4He and 3He switches are off
			turn_off_3He_4He_switches(new_temps,ps)
			start_time = time.time()+sleep_time
			count = -2
		
		new_time = time.time()-start_time
		while new_time < 0: #for haveing a delay in the start hang here until ready to heat 4He pump
			new_time = time.time()-start_time #current time
			new_temps = get_temps()
			_, new_volt, new_curr = read_power_supplies()
			monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
			writeToFile(volt,curr,L,dIdt,Z,new_temps)
			print_pretty(volt,curr,L,dIdt,Z,new_temps)
		
		if count == -2: #heat up the 4He pump
			turn_on_ADR_switch(ps)#turn on the ADR switch at the beginning
			print("Heating up 4He Pump")
			while new_time <30*60:
				new_time = time.time()-start_time #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				heat_4He_pump(new_temps,ps)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
			count = -1
			
		if count == -1: #Heat up the 3He pump keep 4He pump hot
			print("Heating up 3He pump")
			while new_time < 50*60:
				new_time = time.time()-start_time #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				heat_4He_pump(new_temps,ps)
				heat_3He_pump(new_temps,ps)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
			count = 0
			
		if count == 0: #wait until ready to ramp up
			print("Waiting to ramp up")
			while check_start_ramp(new_temps):
				new_time = time.time()-start_time #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				heat_4He_pump(new_temps,ps)
				heat_3He_pump(new_temps,ps)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
			count = 1
		
		if count == 1: #start ramp up
			print("starting ramp up")
			new_temps = get_temps()
			if temp_safety_check(new_temps): #run a safety check on temps before ramping up
				pass
			else:
				print("Did not pass tempearature safety before beginning ramp up exiting program")
				sys.exit()
			dIdt,volt,targ,curr,Z = get_ami_data(ami)
			if magnet_safety_check(dIdt,volt,targ,curr,Z): #run a safety check on the magnet current and resistance
				pass
			else:
				print("Did not pass magnet safety check before beginning ramp up exiting program")
				sys.exit()
				
			start_ramp_time = time.time()
			rampU(ami) #start the ramp up
			while (time.time()-start_ramp_time)< 30*60: #20 mins to ramp and 10 mins for good measure
				new_time = time.time()-start_time  #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				dIdt,volt,targ,curr,Z = get_ami_data(ami)	
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				heat_4He_pump(new_temps,ps) #keep pumps hot during ramp up
				heat_3He_pump(new_temps,ps)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
				if temp_safety_check(new_temps): #temp safety check
					pass
				else:
					emergency_ramp_down(ami)
					count = 6
					break
				if magnet_safety_check(dIdt,volt,targ,curr,Z): #magnet safety check
					pass
				else:
					emergency_ramp_down(ami)
					count = 6
					break
			if count !=6:
				count = 2
			
		if count == 2: # the magnet is energized time to sink the 4He pump:
			print("sinking 4He pump")
			new_temps = get_temps()	
			while new_temps[7] > 5.0: #4He pump It might be better to trigger this when the 4He/3He gets below 2K because when the 
				# 4He head is cold but the 3He pump is hot the 4He charge has to fight the conductino of the 3He hot pump to 4K
				# of course we don't want to sink them at teh same time
				# maybe don't sink it but stop heating it if the 4He and 3He heads are cold
				new_time = time.time()-start_time  #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				dIdt,volt,targ,curr,Z = get_ami_data(ami)
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
				cool_4He_pump(new_temps,ps)
				heat_3He_pump(new_temps,ps)
				if temp_safety_check(new_temps):
					pass
				else:
					ps.change_voltage('He4 switch',0) #turn off 4He switch so that the 4HE pump stop sinking and increassing the 4K plate temp
					emergency_ramp_down(ami)
					count = 6
					break
				if magnet_safety_check(dIdt,volt,targ,curr,Z):
					pass
				else:
					ps.change_voltage('He4 switch',0) #turn off 4He switch so that the 4HE pump stop sinking and increassing the 4K plate temp
					emergency_ramp_down(ami)
					count = 6
					break
			if count != 6:
				count = 3
			
		if count == 3: # the magnet is energized and the 4He pump is sunk, time to sink the 3He pump
			print("sinking 3He pump")
			new_temps = get_temps()	
			while new_temps[8] > 4.5: #3He pump
				new_time = time.time()-start_time  #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				dIdt,volt,targ,curr,Z = get_ami_data(ami)
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
				cool_3He_pump(new_temps,ps)
				if temp_safety_check(new_temps):
					pass
				else:
					ps.change_voltage('He3 switch',0) #turn off 3He switch so that the 4HE pump stop sinking and increassing the 4K plate temp
					emergency_ramp_down(ami)
					count = 6
					break
				if magnet_safety_check(dIdt,volt,targ,curr,Z):
					pass
				else:
					ps.change_voltage('He3 switch',0) #turn off 3He switch so that the 4HE pump stop sinking and increassing the 4K plate temp
					emergency_ramp_down(ami)
					count = 6
					break
			if count !=6:
				count = 4
			
		if count == 4: # both 4H3 and 3He pumpu are sunk turn off the ADR switch
			print("Turning off ADR switch")
			turn_off_ADR_switch(ps)
			new_temps = get_temps()
			while new_temps[12] > 4.5:#adr switch
				new_time = time.time()-start_time  #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				dIdt,volt,targ,curr,Z = get_ami_data(ami)
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)
				if temp_safety_check(new_temps):
					pass
				else:
					emergency_ramp_down(ami)
					count = 6
					break
				if magnet_safety_check(dIdt,volt,targ,curr,Z):
					pass
				else:
					emergency_ramp_down(ami)
					count = 6
					break
			if count != 6:		
				count = 5
			
		if count == 5: # ADR switch is off start ramp down
			print("Starting ramp down") # do i need this
			#ami.write('CONF:CURR:TARG 0\n')
			#ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
			#ami.write('RAMP\n')
			dIdt_old = -0.25/60
			#dIdt = -0.25/60
			#time.sleep(5)
			print('Ramping down at -0.25 A/min.')
			dIdt,volt,targ,curr,Z = get_ami_data(ami)
			#start pid looping
			while curr> 0.001 and dont_stop: #stay here until the current is all depleted or stop() is called			
				new_time = time.time()-start_time #current time
				listen_for_temp_interupt()
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				dIdt,volt,targ,curr,Z = get_ami_data(ami)
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
				writeToFile(volt,curr,L,dIdt,Z,new_temps)
				print_pretty(volt,curr,L,dIdt,Z,new_temps)		

				if running: #to allow for pausing
					if use_pid:
						pid.setpoint = np.float(temp)
						current_temp = new_temps[18]#
						print("")
						print(current_temp)
						print(pid.setpoint)
						dIdt_old = dIdt
						dIdt = pid(current_temp)#
						print(str(dIdt)[0:6])#
						print(str(np.abs(dIdt))[0:6])#
						print("")
						if dIdt>0:#
							ami.write('CONF:CURR:TARG 1.5\n')#
						else:#
							ami.write('CONF:CURR:TARG 0\n')#
						ami.write('CONF:RAMP:RATE:CURR 1,'+str(np.abs(dIdt))[0:6]+',10\n')#
						ami.write('RAMP\n')#
						if dIdt != dIdt_old:
							time.sleep(5) #needs time to equilibrate before measure resistance	
					else:	
						temp_control(new_temps,ami,curr)
				if temp_safety_check(new_temps):
					pass
				else:
					emergency_ramp_down(ami)
					break
				if magnet_safety_check(dIdt,volt,targ,curr,Z):
					pass
				else:
					emergency_ramp_down(ami)
					break
			count = 6
			# just make sure you ramp to zero when you are done	
			ami.write('CONF:CURR:TARG 0\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.5,10\n')
			ami.write('RAMP\n')
				
		if count == 6: # just keep monitoring after the fact
			while True:
				new_time = time.time()-start_time #current time
				new_temps = get_temps()
				_, new_volt, new_curr = read_power_supplies()
				dIdt,volt,targ,curr,Z = get_ami_data(ami)
				monitor_plot.update(new_time, new_temps, new_volt, new_curr, [0],curr)
			
				
					

def turn_on_ADR_switch(ps):
	ps.change_voltage('ADR switch',1.75)
	
def turn_off_ADR_switch(ps):
	ps.change_voltage('ADR switch',0)
		
def turn_off_3He_4He_switches(temps,ps):
	global sleep_time
	ps.change_voltage('He4 switch',0)
	ps.change_voltage('He3 switch',0)
	if temps[9] >10. or temps[10]>10: #he3 and He4 switches
		print("He4 or He3 switch still hot waiting at least 20mins to cool")
		if sleep_time<20*60 and sleep_time>-1:
			sleep_time = 20*60
	
	
def heat_4He_pump(temps,ps):
	#Heat up the 4He pump
	if temps[7]<45.: #4He pump
		ps.change_voltage('He4 pump',25)
	if 50>temps[7]>45.:
		ps.change_voltage('He4 pump',15)
	if temps[7]>50.:
		ps.change_voltage('He4 pump',0)
		
def heat_3He_pump(temps,ps):
	if temps[16] > 2.0 or temps[17] > 2.0: #if the 3He head and 4He head are still hot
		if temps[8]<45.:#3He pump
			ps.change_voltage('He3 pump',15)
		if 50>temps[8]>45.:
			ps.change_voltage('He3 pump',5)
		if temps[8]>50.:
			ps.change_voltage('He3 pump',0)
	else: #the heads are already 4HE cold so no point in heating still
		ps.change_voltage('He3 pump',0)

		
def check_start_ramp(temps): 
	#want to make sure everything is cold before ramping up
	#first check that everything is behaving appropriately if
	if temps[15] > 4.7: #check this temp during cylcle
		return True
	
def temp_safety_check(temps):
	# a general check that everything is not above recommended limits
	if temps[15] >6.5:# the 4K plate should never heat above 6.5K
		return False
	elif temps[1] > 11: # 4K HTS should be lower than 9.2 but need to fix thermomenter routing
		return False
	elif temps[2] > 75: # 50 HTS goes normal at 100K
		return False
	else:
		return True
		
def get_ami_data(ami):
	global dIdt
	dIdt = rampRate()
	ami.write('VOLT:SUPP?\n')
	volt = ami.readline()
	ami.write('CURR:TARG?\n')
	targ = ami.readline()
	#print('Supply V: '+volt )
	volt = float(volt)
	ami.write('CURR:MAG?\n')
	curr = ami.readline()
	#print('Mag I: '+curr)
	curr = float(curr)
	if float(targ)<float(curr):
		dIdt = -dIdt
	if curr > 0.4: #  if curr > 0.05 and volt >0.1: the bummer here is that voltage is only measured to 10mV
		Z = (volt-dIdt*L)/curr
	else:
		Z=0
	return dIdt,volt,targ,curr,Z
		
def magnet_safety_check(dIdt,volt,targ,curr,Z):
	if volt >0.25:
		print("Hitting voltage limit")
		return False
	elif curr > 10.5:
		print("Current too high above 10.5 Amps")
		return False
	elif Z >= 0.050:
		print('Resistance above 0.050 Ohms')
		return False
	else:
		return True
		
def cool_4He_pump(temps,ps):
	if temps[7]>40.: #4He pump
		ps.change_voltage('He4 switch',2) #soft on
	elif temps[7]>20:
		ps.change_voltage('He4 switch',2.2) #not as soft on
	else:
		ps.change_voltage('He4 switch',3.0)	 #on	

def cool_3He_pump(temps,ps):
	if temps[8]>20.: #4He pump
		ps.change_voltage('He3 switch',1.9) #soft on
	else:
		ps.change_voltage('He3 switch',3.0)	 #on		
		
def emergency_ramp_down(ami):
	#ramp down current to zero at 0.5 A/min.
	global running
	running = False
	ami.write('CONF:CURR:TARG 0\n')
	ami.write('CONF:RAMP:RATE:CURR 1,0.50,10\n')
	ami.write('RAMP\n')
	print('Powering Down to 0A at -0.5 A/min.')
	
def rampU(ami): 
	#begin increasing ramp rate
	global dIdt
	#set initial ramp rate to 0.5 A/min to 10A target
	ami.write('CONF:CURR:TARG 10\n')
	ami.write('CONF:RAMP:RATE:CURR 1,0.5,10\n')
	ami.write('RAMP\n')
	dIdt = 0.5/60
	print('Ramping to 10A at 0.5 A/min')

def temp_control(temps,ami,curr):
	global dIdt
	#Ramp down to zero at varying rates based on target temp
	#temp must be converted to float each time b/c Tkinter is not thread-safe
	if  temps[18] > float(temp) + 0.3 and temps[18]!=-1:
		#print("ramp state 1")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.25/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif  float(temp)+0.3> temps[18] > float(temp) + 0.1 and temps[18]!=-1:
		#print("ramp state 2")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.25/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)+0.1 > temps[18] >= float(temp) + 0.05 and temps[18]!=-1:
		#print("ramp state 3")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.1,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.1/60:#.25 trying to slow it down
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)+ 0.05 > temps[18] >= float(temp) + 0.01 and temps[18]!=-1:
		#print("ramp state 4")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.1,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.1/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)+0.01 > temps[18] >= float(temp) + 0.005 and temps[18]!=-1:
		#print("ramp state 5")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.05,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.05/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)+0.005 > temps[18] >= float(temp) + 0.002 and temps[18]!=-1:
		#print("ramp state 6")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.01,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.01/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)+0.002 > temps[18] >= float(temp) + 0.001 and temps[18]!=-1:
		#print("ramp state 7")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.005,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.005/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)+0.001 > temps[18] >= float(temp)+0.0001 and temps[18]!=-1:
		#print("ramp state 8")
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.001,10\n')
		ami.write('RAMP\n')
		if dIdt != -0.001/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif float(temp)-0.005 < temps[18] <= float(temp)- 0.002 and temps[18]!=-1:
		#print("ramp state 9")
		amp = curr+1
		command = 'CONF:CURR:TARG '+str(amp)+'\n'
		ami.write(command)
		ami.write('CONF:RAMP:RATE:CURR 1,0.01,10\n')
		ami.write('RAMP\n')
		if dIdt != 0.01/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif temps[18] <= float(temp)- 0.005 and temps[18]!=-1:
		#print("ramp state 10")
		amp = curr+1
		command = 'CONF:CURR:TARG '+str(amp)+'\n'
		ami.write(command)
		ami.write('CONF:RAMP:RATE:CURR 1,0.05,10\n')
		ami.write('RAMP\n')
		if dIdt != 0.05/60:
			time.sleep(5) #needs time to equilibrate before measure resistance
	elif temps[18]!=-1:
		#print("ramp state 11")
		ami.write('PAUSE\n')
		dIdt = 0
		time.sleep(5)
				
def listen_for_temp_interupt():
	global interrupt_server
	global tk_app
	global temp
	new_inter_temp = interrupt_server.poll()
	if new_inter_temp is not None:
		print('> Received interrupt packet, changing temp to {} K.'.format(new_inter_temp))
		temp = new_inter_temp
		tk_app.myentry.delete(0, END)
		tk_app.myentry.insert(END, str(new_inter_temp))
		
def print_pretty(volt,curr,L,dIdt,Z,temps):
	print("")#newline
	print(' Supply V: '+str(volt+.000001)[0:6],end='')#the +.0001 makes sure i doesn't round off a zero at the end for the string
	print(' Mag I: '+str(curr+.000001)[0:6],end='')
	print(' Z: ' + str(Z*1000.+.0000001)[0:4] + ' mOhms',end='')
	print(' ADR T: '+str(temps[18]+.0000001)[0:6],end='')
	print(' 4K HTS: '+str(temps[1]+.0000001)[0:5],end='')
	print(' 4K Plate: '+str(temps[15]+.000001)[0:5],end='')
	print(' 50K HTS: '+str(temps[2]+.0000001)[0:5],end='')
	print(' He-3: '+str(temps[16]+.0000001)[0:5],end='')
	print(' He-4: '+str(temps[17]+.00000001)[0:5],end='')
	
def rampRate():
	global rate
	ami.write('STATE?\n')
	state = ami.readline()
	state = int(state)
	
	#print(state)
	#S1: RAMPING to target current'
	#S4: Ramping in MANUAL UP mode
	#S5: Ramping in MANUAL DOWN mode
	if state == 1:
		print(' RAMPING',end='')
		ami.write('RAMP:RATE:CURR: 1?\n')
		strng = ami.readline()
		a = strng.split(',')
		rate = float(a[0])/60
	else:
		print(' PAUSED',end='')
		rate = 0
	print(' dIdt: ' + str(rate*1000.)[0:5] + ' mA/sec',end='')
	return rate

def alarm():
	global Alarm
	if Alarm != 0: #if the alarm is turned on proceed
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
		
		
def setTarg(self):
	global temp
	temp = self.temp.get()
	content = self.temp.get()
	print("")
	print('The temperature is set at: ' + str(temp) + 'K')
	#return temp
	
def setPID(self):
	global pid
	pid.Kp = np.float(self.Kp.get())
	pid.Ki = np.float(self.Ki.get())
	pid.Kd = np.float(self.Kd.get())
	print("Changing pid tunings")
		
def stop(): #have to think about this wont break in main() id in another while loop when count = 5
	# almost the same as emergency ramp down but might what differente rates eventually
	#ramp down current to zero at 0.5 A/min.
	global count
	global dont_stop #cant stop
	dont_stop = False
	count = 6
	ami.write('CONF:CURR:TARG 0\n')
	ami.write('CONF:RAMP:RATE:CURR 1,0.50,10\n')
	ami.write('RAMP\n')
	print('Powering Down to 0A at -0.5 A/min.')
	
def pause(): #needs to be fixed
	global running
	if running == False:
		running = True
		print('Resuming')
		#start() 
	else:
		running = False
		print('Pausing..')
		time.sleep(5) #wait a moment to make sure that we are not in the middle of issusing a ramp command to the ami
		ami.write('PAUSE\n')
		
def start():
	print('Starting cycle')
	print("count = ", count)
	new_thread = threading.Thread(target = main)
	new_thread.start()

def status():
	try:
		ami.write('STATE?\n')
		state = ami.readline()
		state = int(state)
		if state == 1:
			print('RAMPING to target current')
		if state == 2:
			print('HOLDING at the target current')
		if state == 3:
			print('PAUSED')
		if state == 4:
			print('Ramping in MANUAL UP mode')
		if state == 5:
			print('Ramping in MANUAL DOWN mode')
		if state == 6:
			print('ZEROING CURRENT')
		if state == 7:
			print('Quench Detected')
		if state == 8:
			print('At ZERO current')
		if state == 9:
			print('Heating persistent switch')
		if state == 10:
			print('Cooling persistent switch')
		ami.write('*ETE 111\n')
		ami.write('*TRG\n')
		trigger = ami.readline()
		print(trigger)

		ami.write('VOLT:LIM?\n')
		print('Voltage Limit: ')
		vlim = ami.readline()
		print(vlim)
		ami.write('CURR:TARG?\n')
		print('Target: ')
		targ = ami.readline()
		print(targ)
		ami.write('RAMP:RATE:CURR:1?\n')
		print('I RampRate, I limit: ')
		currRampRate = ami.readline()
		print(currRampRate)
		
		print('Target Temperature: '+str(temp)+'K')
	except Exception as e: 
		print(e) 
		print('Unable to query AMI, do not proceed')

def writeToFile(volt,curr,L,dIdt,Z,y):
	global first
	#print('Writing to file... ')
	now = datetime.datetime.now()
	if first: #if it is the first time writing to file put in a header
		writer.writerow(['Date-LocalTime', 'Voltage(V)', 'Current(A)', 'Inductance(H)', 'dI/dt', 'Resistance(Ohms)', 'ADR temp'])
	writer.writerow([now,volt,curr,L,dIdt,Z,y[18]])
	first = False

def setDelay(self):
	global sleep_time
	d = self.delay.get()
	hours_minutes = d.split(':')
	hrs = hours_minutes[0]
	mnts = hours_minutes[1]
	sleep_time = int(hrs)*3600 + int(mnts)*60

class App:
	#GUI
	def __init__(self):
		global auto_start

		self.master = Tk()
		self.master.title('ADR Controller')
		self.temp = StringVar()
		self.Kp = StringVar()
		self.Ki = StringVar()
		self.Kd = StringVar()
		#temp = self.temp.get()
		#print(temp)
		self.delay = StringVar()

		self.label1 = Label(self.master, text='TEMPERATURE CONTROL', font=('Impact', 12))
		self.label1.grid(row=0, column=0, pady=5, padx=10)

		self.button1 = Button(self.master,text='Set Temperature', command = lambda: setTarg(self), activebackground = 'purple')
		self.button1.grid(row=2,column=0, padx=5)

		self.label2 = Label(self.master, text='RAMP CONTROL', font=('Impact', 12))
		self.label2.grid(row=3, column=0, pady=5, padx=10)

		self.button2 = Button(self.master,text= 'Ramp to Zero', command = stop, activebackground = 'purple')
		self.button2.grid(row=4,column=2)

		self.button3 = Button(self.master,text= 'Start', command = start, activebackground = 'purple')
		self.button3.grid(row=4,column=0)

		self.button4 = Button(self.master,text= 'Pause/Resume', command = pause, activebackground = 'purple')
		self.button4.grid(row=4,column=1)

		self.button5 = Button(self.master,text= 'Status', command = status, activebackground = 'purple')
		self.button5.grid(row=4,column=3)

		self.myentry = Entry(self.master, textvariable=self.temp)
		self.myentry.grid(row=1, column=0)
		#self.myentry.pack()
		self.myentry.insert(END,"0.1")
		self.button1.invoke()
		#self.button1.invoke()
		#content = self.temp.get()
		#print(content)
		
		#PID gui stuff
		self.label_pid = Label(self.master, text='PID CONTROL', font=('Impact', 12))
		self.label_pid.grid(row=0, column=4, pady=5, padx=10)
		
		self.label_Kp = Label(self.master, text='Kp')
		self.label_Kp.grid(row=1, column=3, pady=5, padx=10)
		
		self.label_Ki = Label(self.master, text='Ki')
		self.label_Ki.grid(row=1, column=4, pady=5, padx=10)
		
		self.label_Kd = Label(self.master, text='Kd')
		self.label_Kd.grid(row=1, column=5, pady=5, padx=10)
		
		self.myentry_Kp = Entry(self.master, textvariable=self.Kp)
		self.myentry_Kp.grid(row=2, column=3)
		self.myentry_Kp.insert(END,"0.01")
		
		self.myentry_Ki = Entry(self.master, textvariable=self.Ki)
		self.myentry_Ki.grid(row=2, column=4)
		self.myentry_Ki.insert(END,"0.00")
		
		self.myentry_Kd = Entry(self.master, textvariable=self.Kd)
		self.myentry_Kd.grid(row=2, column=5)
		self.myentry_Kd.insert(END,"0.00")
		
		self.button_pid = Button(self.master,text='Set PID Parameters', command = lambda: setPID(self), activebackground = 'purple')
		self.button_pid.grid(row=3,column=4, padx=5)

		#self.button7 = Button(self.master,text= 'SwitchOff', command = turn_off_ADR_switch, activebackground = 'purple')
		#self.button7.grid(row=4,column=5)
		
		#self.button8 = Button(self.master,text= 'Run Fridge', command = startFridge, activebackground = 'purple')
		#self.button8.grid(row=2,column=5)
		#self.myentry.insert(END, 'Type Temp Here')
		
		self.button9 = Button(self.master,text='Set Delay', command = lambda: setDelay(self), activebackground = 'purple')
		self.button9.grid(row=2,column=2, padx=5)
		
		self.myentry2 = Entry(self.master, textvariable=self.delay, text='hrs:min')
		self.myentry2.grid(row=1, column=2)
		#self.counter = 0
		if auto_start == 1:
			print("auto starting")
			self.button3.invoke()
			
		global monitor_plot
		monitor_plot = MonitorPlot(sleep_interval, 420, plot_pressure=False,plot_magnet = True)
		monitor_plot.show()
		self.master.mainloop()



interrupt_server.open()
tk_app = App()

interrupt_server.close()
ami.close()
csvfile.close()
