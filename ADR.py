from __future__ import print_function
import visa
import serial
import time
import os
import datetime
from functions import get_temps
import csv
import threading
from Tkinter import *
import argparse

from ADRinterrupt import InterruptServer


#TO DO:
#Optimize code for stable ADR temp
#     average some number of ADR temp measurements before deciding to change the ramp rate
# add some faster up ramps for when you want to ramp back up to a hotter temp

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
'''
READ ME:
This script is written to be run after fridge_cycle.py and the ADR switch off.
It follows Addi's recipe for cooling the ADR down, ADR_cycle_soft_heatswitch_on.pdf. To run the script using the GUI:
1) Set the desired temperature you want the ADR to run at. (This can be changed while running the code.)
2) Hit Start to begin the script. The ADR switch will be powered until the He-4 and He-3 heads
   equilibrate below 1.1K. It then shuts off the switch and begins the ramping cycle. The ramping cycle
   is controlled by continous runs of the check() function which monitors temp and resistance. It will
   alert the Alarm() and stop() functions if wrong conditions are met.
   The temperature of the ADR is controlled by varying rates of applied current based on distance from
   the desired temp. *These numbers will have to be tweaked later for better results and when mass changes are made.
3) The PAUSE function, causes the script to pause, as well as the AMI to hold at the current. You can resume the script 
	hitting the button again.
4) If you are past the initial ramping up stage of the cycle and the ADR is cold, you can use the RAMPDOWN button to skip
	to ramping down.
   NOTES:
*   To safegaurd the magnet, the code has a number of try statements whenever there is a serial command that could possibly return an error.
	If one of these try statements fail, it will call the stop function which will ramp down to zero current at 0.5 A/min and trigger the alarm.

*	Set delay takes input in form of 'hours:minutes' i.e 10:30 will run in 10hrs and 30min from pushing start

Code is run by moving from state to state as indicated by count
count = 0 => waiting for user to start the ADR cycle
count = 1 => Turn oan ADR switch and wait for it to heat up
count = 2 => seems to be the same as count=1 not used anymore?
when everything is the right temp proceed to 
count = 3 => start ramp up to 10A
count = 4 => monitor and wait until he4 and ADR cool
count = 5 => turn of ADR switch and wait for it to cool
count = 6 => start ramp down 
count = 7 => ramp down state stay at specified temperature

'''
auto_start = 1 #0 don't auto start 1 do auto start

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

Alarm = 0
temp = 0
L = 16 #magnet Inductance
running = True
first = True
count = init_count() # Allows count to be set with a command line argument
t=0
t0=0
sleep_time = 0
fiftyK = range(0,1)
dIdt = 0
tk_app = None

# create (but dont open) the interrupt server
interrupt_server = InterruptServer(password='')

#open connection to ADR switch power supply
rm = visa.ResourceManager()
ag49 = rm.open_resource('GPIB1::3::INSTR') #power supply 3647 on top row of rack
ag49.write('OUTPut ON')
#connect to AMI controller
ami = serial.Serial('COM6', 115200, rtscts=1)
ami.write('SYST:LOC\n')

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
	global t0
	#The Model 430 Programmer uses the following parameters related to the
	#RS-232 interface:
	# Baud Rate: 115200
	# Parity: No Parity
	# Data Bits: 8 Data Bits
	# Number of Start Bits: 1 bit
	# Number of Stop Bits: 1 bit
	# Flow Control: Hardware (RTS/CTS)
	time.sleep(sleep_time)
	#Returns '0' for ramp rates displayed/specified in terms of seconds, or '1' for minutes.
	ami.write('RAMP:RATE:UNITS?\n')
	unit = ami.readline()
	unit = int(unit)
	if unit == 0:
		print('Ramp rate is in seconds')
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

	#turn on ADR Switch
	if count == 0:
		switchOn()
	#begin ramp up
	if unit == 1:
		try:
			t0 = time.time()
			rampU()
		except:
			stop()
			alarm()
			print('Error: Unable to begin ramp Up')

	else:
		print('Please set units to A/min.')



def switchOn():
	global running
	global count
	
	while running:
		#keep ADR switch on until desired conditions
		try:
			temps = get_temps()
			print("")#newline
			print(' He3 Temp: ',end='')
			print(temps[16],end='')
			print(' He4 Temp: ',end='')
			print(temps[17],end='')
			print(' ADR Temp: ',end='')
			print(temps[18],end='')
			print(' ADR switch Temp: ',end='')
			print(temps[12],end='')
			#If ADR is already on...
			#if -1< temps[18] <1.25:
			#	count = 2
			### POTENTIAL BUG BELOW (incorrect use of `and` with `temps[16] and temps[17]``)
			if temps[16] and temps[17] < 1.3 and temps[18]!=-1 and count == 0:
				#if He3 and He4 are below 1.3K turn on ADR switch
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.75')
				#3.5 #Afyhrie changed from 1.75 to 1.5 on June 28 2017
				#to make sure the ADR switch doesn't heat above 17 K
				print('ADR switch ON')
				count=1
			if 17.2 > temps[12] > 17.0 and count == 1:
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.6')
				#count=2
			if 17 > temps[12] > 16.8 and count == 1:
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.68')
				#count=2
			if 16.8 > temps[12] > 15 and count == 1:
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.75')
			if temps[18] <1.4 and temps[17] < 1.3 and temps[18]!=-1 and count == 1 and temps[12]>16.8:#1.25 1.15
				#wait till He4/ADR return to normal temp. before switch
				print('ADR and He4 Stabalized')
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.65')
				count=3
				break
			if temps[12] > 17.2:
				print('ADR switch above 17.2K')
				switchOff()
				count = 1
				#running = False
				#break
		except:
			#if get_temps fails, turn off ADR switch to prevent overheating
			running = False
			switchOff()
			alarm()
			print('Error occured while running Switch ON')
			break
		time.sleep(3)
def switchOff():
	#turn off ADR switch
	ag49.write('INST:SEL OUT1')
	ag49.write('Volt 0')
	print("")#newline
	print('ADR switch OFF')

def rampU():
	#begin increasing ramp rate
	global count
	global dIdt
	
	if check() == True and running and count==3:
		#set initial ramp rate to 0.5 A/min to 10A target
		ami.write('CONF:CURR:TARG 10\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.5,10\n')
		ami.write('RAMP\n')
		dIdt = 0.5/60
		count=4
		print('Ramping to 10A at 0.5 A/min')
		#infinite loop b/c check becomes driver function
		while check() == True and running:
			pass
	else:
		print('Check Temperatures or Resistance')

def rampD():
	global count
	global dIdt
	switchOff()
	#ramp down to 8A at 0.25 A/min
	#Move this into while loop?
	if count==6:
		ami.write('CONF:CURR:TARG 0\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
		ami.write('RAMP\n')
		dIdt = -0.25/60
		print('Ramping down at -0.25 A/min.')
		#while check()==True and rampRate()!=0 and running:
		#while check()==True and rampRate()!=0 and running:
		#	pass
		count=7
	#try:
	while check()==True and running:
		#temps = get_temps()
		
		if temps[17]>1.7:
			alarm()
			print('He4 above 1.7K')
		if temps[17]>1.7:#1.5
			stop()
			print('He4 Above 1.7K')
		if temps[18]>2.0:
			alarm()
			print('ADR above 1.7K')
		if temps[18]>3.0:#1.5
			stop()
			print('ADR above 3.0K')
			
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
			time.sleep(1)
  

def check():
	#check cryostat temperatures and mag resistance
	#also driver function for ramping
	# This function runs when count == 3 (once), 4 (loop), or 7 (loop)
	global count
	global t
	global temps
	global curr
	global fiftyK
	global dIdt
	global interrupt_server
	global temp
	global tk_app

	new_inter_temp = interrupt_server.poll()
	if new_inter_temp is not None:
		print('> Received interrupt packet, changing temp to {} K.'.format(new_inter_temp))
		temp = new_inter_temp
		tk_app.myentry.delete(0, END)
		tk_app.myentry.insert(END, str(new_inter_temp))
	
	try:
		t = time.time() - t0
		temps1 = get_temps()
		#get ramp rate
		dIdt = rampRate()
		#time.sleep(1) #Jordan removed this  
		temps2 = get_temps() #using get_temps as time.sleep(1) 
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
		temps3 = get_temps() #using get_temps as time.sleep(1)
		
		temps = (temps1+temps2+temps3)/3.
		
		#calculate resistance
		#When current is very low, Z>>0.025
		#the condition should be on current only?
		if float(targ)<float(curr):
			dIdt = -dIdt
		if curr > 0.4: #  if curr > 0.05 and volt >0.1: the bummer here is that voltage is only measured to 10mV
				Z = (volt-dIdt*L)/curr
		else:
			Z=0
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
		#print('t: '+str(t))
		
		#4k HTS
		if temps[1] > 8:
			alarm()
		if temps[1] > 8.5:
			stop()
		#4k Plate
		if temps[15] > 5:
			alarm()
		if temps[15] > 6:
			stop()
		#50k HTS
		fiftyK.append(temps[2])
		if first==False:
			d50K = fiftyK[1]-fiftyK[0]
		else:
			d50K = 0
		fiftyK[0] = fiftyK.pop()
		#print(d50K)
		if d50K>0.001:
			alarm()
		if d50K>0.05:
			#reads in ~5sec intervals
			print('dT/dt of 50K HTS > 0.6K/min')
			stop()
		if temps[2] > 61:
			alarm()
		if temps[2] > 70:
			stop()
		
		#write to file
		writeToFile(volt,curr,L,dIdt,Z,temps)
		
		#ensure switch doesn't over/under heat during stage 4
		if temps[12]>17.3 and count==4:
			switchOff()
		elif 17.0<temps[12]<17.3 and count==4:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 1.6')
		elif 16.8<temps[12]<17.0 and count==4:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 1.67')
		elif temps[12]<16.8 and count==4:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 1.73')	
		print(' ADR Switch Temp: ' + str(temps[12]+.00001)[0:5],end='')
	
		
		#turn off ADR switch if He-4 Head and ADR cool to 1.2K, wait 5 minutes from start of ramping
		#wait because initially temperature will be low before switch
		if temps[18]<1.4 and temps[17] < 1.3 and temps[18]!=-1 and t>5.0*60.0 and count==4:#1.3,1.2
			count=5
			switchOff()

		#ADR Switch temp and begin ramp down
		if temps[12] < 4.2 and count == 5:
			count=6
			rampD()
			return False
		
		#check magnet resistance
		if Z >= 0.050:
			print('Resistance above 0.050 Ohms')
			stop()
			switchOff()
			return False

		else:
			#time.sleep(1) #Jordan removed compensated by longer get_temps but ami needs this
			return True
		
	except Exception as e: 
		print(e) 
		#print('Error Occured while checking temp. or resistance.')
		stop()
		switchOff()
		alarm()
		return False
'''
def rampState():
	ami.write('STATE?\n')
	state = ami.readline()
	state = int(state) 
	return state
'''
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
	print('The temperature is set at: ' + str(temp) + 'K')
	#return temp
def stop():
	#ramp down current to zero at 0.5 A/min.
	global running
	running = False
	ami.write('CONF:CURR:TARG 0\n')
	ami.write('CONF:RAMP:RATE:CURR 1,0.50,10\n')
	ami.write('RAMP\n')
	print('Powering Down to 0A at -0.5 A/min.')
def pause():
	global running
	if running == False:
		running = True
		print('Resuming')
		start() #AF may 2018 try un-commenting this out to get the 'resume' function to work
	else:
		running = False
		print('Pausing..')
		ami.write('PAUSE\n')
		
def start():
	print('Starting AMI')
	if count==0:
		new_thread = threading.Thread(target = main)
	elif count==1:
		new_thread = threading.Thread(target = switchOn)
	elif count==2:
		new_thread = threading.Thread(target = switchOn)
	elif count==3:
		new_thread = threading.Thread(target = rampU)
	elif count==4:
		new_thread = threading.Thread(target = rampU)
	elif count==5:
		new_thread = threading.Thread(target = rampU)
	elif count==6:
		new_thread = threading.Thread(target = rampD)
	elif count==7:
		new_thread = threading.Thread(target = rampD)
	else:
		print('Cycle Complete')
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
def rD():
	global running
	running = True
	new_thread = threading.Thread(target = rampD)	
	new_thread.start()
#def startFridge():
#	execfile('fridge_cycle.py')
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
		self.delay = StringVar()

		self.label1 = Label(self.master, text='TEMPERATURE CONTROL', font=('Impact', 12))
		self.label1.grid(row=0, column=0, pady=5, padx=10)

		self.button1 = Button(self.master,text='Set Temperature', command = lambda: setTarg(self), activebackground = 'purple')
		self.button1.grid(row=2,column=0, padx=5)

		self.label2 = Label(self.master, text='RAMP CONTROL', font=('Impact', 12))
		self.label2.grid(row=3, column=0, pady=5, padx=10)

		self.button2 = Button(self.master,text= 'STOP', command = stop, activebackground = 'purple')
		self.button2.grid(row=4,column=2)

		self.button3 = Button(self.master,text= 'Start Ramp', command = start, activebackground = 'purple')
		self.button3.grid(row=4,column=0)

		self.button4 = Button(self.master,text= 'Pause/Resume', command = pause, activebackground = 'purple')
		self.button4.grid(row=4,column=1)

		self.button5 = Button(self.master,text= 'Status', command = status, activebackground = 'purple')
		self.button5.grid(row=4,column=3)

		self.myentry = Entry(self.master, textvariable=self.temp)
		self.myentry.grid(row=1, column=0)
		self.myentry.insert(END,"0.1")
		self.button1.invoke()
		#self.button1.invoke()
		
		self.button6 = Button(self.master,text= 'RampDown', command = rD, activebackground = 'purple')
		self.button6.grid(row=4,column=4)

		self.button7 = Button(self.master,text= 'SwitchOff', command = switchOff, activebackground = 'purple')
		self.button7.grid(row=4,column=5)
		
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
		self.master.mainloop()


interrupt_server.open()
tk_app = App()
interrupt_server.close()
ami.close()
csvfile.close()
