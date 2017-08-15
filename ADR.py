import visa
import serial
import time
import os
import datetime
from functions import get_temps
import csv
import threading
from Tkinter import *


#written by Tim Childers to run ADR cooling script 18/07/2017

#To Do:
#calibrate ramp rates
#double check safegaurds
#ramp down stages
#check stages of ramping 1 or 2
#rampRate() make sure ramp rate is not zero
#add DeltT of 50K HTS


'''
READ ME:
This script is written to be run with fridge_cycle.py and the ADR switch off.
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
'''

Alarm = 0
count = 0
temp = 0
L = 16 #magnet Inductance
running = True
first = True
count=0
t=0
t0=0
fiftyK = range(0,1)
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
	
	#Returns '0' for ramp rates displayed/specified in terms of seconds, or '1' for minutes.
	ami.write('RAMP:RATE:UNITS?\n')
	unit = ami.readline()
	unit = int(unit)
	if unit == 0:
		print 'Ramp rate is in seconds'
	if unit == 1:
		print 'Ramp rate is in minutes'
	#Sets voltage limit to 0.25V, may need to be higher depending on ramp rate.
	ami.write('CONF:VOLT:LIM 0.25\n')
	ami.write('VOLT:LIM?\n')
	voltLim = ami.readline()
	print 'Voltage limit: '
	print voltLim
	#Returns the target current setting in amperes.
	ami.write('CURR:TARG?\n')
	targ = ami.readline()
	print 'Target: '
	print targ

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
			print 'Error: Unable to begin ramp Up'

	else:
		print 'Please set units to A/min.'



def switchOn():
	global running
	global count
	
	while running:
		#keep ADR switch on until desired conditions
		try:
			temps = get_temps()
			print 'He3 Temp: '
			print temps[16]
			print 'He4 Temp: '
			print temps[17]
			print 'ADR Temp: '
			print temps[18]
			print 'ADR switch Temp: '
			print temps[12]
			#If ADR is already on...
			#if -1< temps[18] <1.25:
			#	count = 2
			if temps[16] and temps[17] < 1.3 and temps[17]!=-1 and count == 0:
				#if He3 and He4 are below 1.3K turn on ADR switch
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.75')
				#3.5 #Afyhrie changed from 1.75 to 1.5 on June 28 2017
				#to make sure the ADR switch doesn't heat above 17 K
				print 'ADR switch ON'
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
				ag49.write('Volt 1.7')
			if temps[18] <1.25 and temps[17] < 1.15 and temps[18]!=-1 and count == 1 and temps[12]>16.8:
				#wait till He4/ADR return to normal temp. before switch
				print 'ADR and He4 Stabalized'
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 1.65')
				count=3
				break
			if temps[12] > 17.2:
				print 'ADR switch above 17.2K'
				switchOff()
				count = 1
				#running = False
				#break
		except:
			#if get_temps fails, turn off ADR switch to prevent overheating
			running = False
			switchOff()
			alarm()
			print 'Error occured while running Switch ON'
			break
		time.sleep(3)
def switchOff():
	#turn off ADR switch
	ag49.write('INST:SEL OUT1')
	ag49.write('Volt 0')
	print 'ADR switch OFF'

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
		print 'Ramping to 10A at 0.5 A/min'
		#infite loop b/c check becomes driver function
		while check() == True and running:
			pass
	else:
		print 'Check Temperatures or Resistance'

def rampD():
	global count
	global dIdt
	switchOff()
	#ramp down to 8A at 0.25 A/min
	#Move this into while loop?
	if count==6:
		ami.write('CONF:CURR:TARG 8\n')
		ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
		ami.write('RAMP\n')
		dIdt = 0.25/60
		print 'Ramping to 2A at -0.25 A/min.'
		#while check()==True and rampRate()!=0 and running:
		while check()==True and rampRate!=0 and running:
			pass
		count=7
	#try:
	while check()==True and running:
		#temps = get_temps()
		#Ramp down to zero at varying rates based on target temp
		#temp must be converted to float each time b/c Tkinter is not thread-safe
		if  temps[18] > float(temp) + 0.3 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 1\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
			ami.write('RAMP\n')
			dIdt = 0.25/60
		if  float(temp)+0.3> temps[18] > float(temp) + 0.1 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 0.1\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
			ami.write('RAMP\n')
			dIdt = 0.25/60
		elif float(temp)+0.1 > temps[18] >= float(temp) + 0.05 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 0\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.25,10\n')
			ami.write('RAMP\n')
			dIdt = 0.25/60
		elif float(temp)+ 0.05 > temps[18] >= float(temp) + 0.01 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 0\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.1,10\n')
			ami.write('RAMP\n')
			dIdt = 0.1/60
		elif float(temp)+0.01 > temps[18] >= float(temp) + 0.005 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 0\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.05,10\n')
			ami.write('RAMP\n')
			dIdt = 0.01/60
		elif float(temp)+0.005 > temps[18] >= float(temp) + 0.002 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 0\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.01,10\n')
			ami.write('RAMP\n')
			dIdt = 0.005/60
		elif float(temp)+0.002 > temps[18] >= float(temp) + 0.001 and temps[18]!=-1:
			ami.write('CONF:CURR:TARG 0\n')
			ami.write('CONF:RAMP:RATE:CURR 1,0.005,10\n')
			ami.write('RAMP\n')
			dIdt = 0.001/60
		elif temps[18] <= float(temp)- 0.002 and temps[18]!=-1:
			amp = curr+1
			command = 'CONF:CURR:TARG '+str(amp)+'\n'
			ami.write(command)
			ami.write('CONF:RAMP:RATE:CURR 1,0.01,10\n')
			ami.write('RAMP\n')
			dIdt = 0.01/60
		elif temps[18]!=-1:
			ami.write('PAUSE\n')
			dIdt = 0
			time.sleep(1)
  

def check():
	#check cryostat temperatures and mag resistance
	#also driver function for ramping
	global count
	global t
	global temps
	global curr
	global fiftyK
	
	try:
		t = time.time() - t0
		temps = get_temps()
		#get ramp rate
		dIdt = rampRate()
		time.sleep(1)
		ami.write('VOLT:SUPP?\n')
		volt = ami.readline()
		#print 'Supply V: '+volt 
		volt = float(volt)
		ami.write('CURR:MAG?\n')
		curr = ami.readline()
		#print 'Mag I: '+curr
		curr = float(curr)
		
		#calculate resistance
		#When current is very low, Z>>0.025
		if curr > 0.05 and volt >0.1:
			Z = (volt-dIdt*L)/curr
		else:
			Z=0
		print 'Supply V: '+str(volt)
		print 'Mag I: '+str(curr)
		print 'Z: ' + str(Z) + ' Ohms'
		print 'ADR T: '+str(temps[18])
		print '4K HTS: '+str(temps[1])
		print '4K Plate: '+str(temps[15])
		print '50K HTS: '+str(temps[2])
		print 'He-3: '+str(temps[16])
		print 'He-4: '+str(temps[17])
		#print 't: '+str(t)
		
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
		print d50K
		if d50K>0.001:
			alarm()
		if d50K>0.05:
			#reads in ~5sec intervals
			print 'dT/dt of 50K HTS > 0.6K/min'
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
			ag49.write('Volt 1.65')
		elif temps[12]<16.8 and count==4:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 1.7')	
		print 'ADR Switch Temp: ' + str(temps[12])
	
		
		#turn off ADR switch if He-4 Head and ADR cool to 1.2K, wait 5 minutes from start of ramping
		#wait because initially temperature will be low before switch
		if temps[18]<1.3 and temps[17] < 1. and temps[18]!=-1 and t>5.0*60.0 and count==4:
			count=5
			switchOff()

		#ADR Switch temp and begin ramp down
		if temps[12] < 4 and count == 5:
			count=6
			rampD()
			return False
		
		#check magnet resistance
		if Z >= 0.050:
			print 'Resistance above 0.025 Ohms'
			stop()
			switchOff()
			return False

		else:
			time.sleep(1)
			return True
		
	except Exception as e: 
		print e 
		#print 'Error Occured while checking temp. or resistance.'
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
	
	#print state
	#S1: RAMPING to target current'
	#S4: Ramping in MANUAL UP mode
	#S5: Ramping in MANUAL DOWN mode
	if state == 1:
		print 'RAMPING'
		ami.write('RAMP:RATE:CURR: 1?\n')
		strng = ami.readline()
		a = strng.split(',')
		rate = float(a[0])/60
	else:
		print 'PAUSED'
		rate = 0
	print 'dIdt: ' + str(rate) + ' A/sec'
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
	print 'The temperature is set at: ' + str(temp) + 'K'
	#return temp
def stop():
	#ramp down current to zero at 0.5 A/min.
	global running
	running = False
	ami.write('CONF:CURR:TARG 0\n')
	ami.write('CONF:RAMP:RATE:CURR 1,0.50,10\n')
	ami.write('RAMP\n')
	print 'Powering Down to 0A at -0.5 A/min.'
def pause():
	global running
	if running == False:
		running= True
		print 'Resuming'
		#start()
	else:
		running = False
		print 'Pausing..'
		ami.write('PAUSE\n')
		
def start():
	print 'Starting AMI'
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
		print 'Cycle Complete'
	new_thread.start()


def status():
	try:
		ami.write('STATE?\n')
		state = ami.readline()
		state = int(state)
		if state == 1:
			print 'RAMPING to target current'
		if state == 2:
			print 'HOLDING at the target current'
		if state == 3:
			print 'PAUSED'
		if state == 4:
			print 'Ramping in MANUAL UP mode'
		if state == 5:
			print 'Ramping in MANUAL DOWN mode'
		if state == 6:
			print 'ZEROING CURRENT'
		if state == 7:
			print 'Quench Detected'
		if state == 8:
			print 'At ZERO current'
		if state == 9:
			print 'Heating persistent switch'
		if state == 10:
			print 'Cooling persistent switch'
		ami.write('*ETE 111\n')
		ami.write('*TRG\n')
		trigger = ami.readline()
		print trigger

		ami.write('VOLT:LIM?\n')
		print 'Voltage Limit: '
		vlim = ami.readline()
		print vlim
		ami.write('CURR:TARG?\n')
		print 'Target: '
		targ = ami.readline()
		print targ
		ami.write('RAMP:RATE:CURR:1?\n')
		print 'I RampRate, I limit: '
		currRampRate = ami.readline()
		print currRampRate
		
		print 'Target Temperature: '+str(temp)+'K'
	except Exception as e: 
		print e 
		print 'Unable to query AMI, do not proceed'

def writeToFile(volt,curr,L,dIdt,Z,y):
	global first
	#print 'Writing to file... '
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



class App:
	#GUI
	def __init__(self):
		self.master = Tk()
		self.master.title('ADR Controller')
		self.temp = StringVar()

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

		self.button4 = Button(self.master,text= 'Pause', command = pause, activebackground = 'purple')
		self.button4.grid(row=4,column=1)

		self.button5 = Button(self.master,text= 'Status', command = status, activebackground = 'purple')
		self.button5.grid(row=4,column=3)

		self.myentry = Entry(self.master, textvariable=self.temp)
		self.myentry.grid(row=1, column=0)
		
		self.button5 = Button(self.master,text= 'RampDown', command = rD, activebackground = 'purple')
		self.button5.grid(row=4,column=4)

		self.button5 = Button(self.master,text= 'SwitchOff', command = switchOff, activebackground = 'purple')
		self.button5.grid(row=4,column=5)
		#self.myentry.insert(END, 'Type Temp Here')

		#self.counter = 0
		self.master.mainloop()


App()
ami.close()
csvfile.close()
