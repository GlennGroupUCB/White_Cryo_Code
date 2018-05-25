import visa
import serial
import time
import threading
from functions import get_temps
from Tkinter import *

#Created by Tim Childers 17/07/2017
#TO DO:
#change returns to ints
#upperbound sparse line on ramp rate querries
#set current max = 10
#no ramp down
#print temp
#He4 alarm
'''
READ ME:
ALWAYS ALWAYS query the AMI before sending any command to ensure:
	1. Units are in A/minute
	2. The serial is responsive and won't timeout
	3. Other parameters are set correctly (max V, etc.)
To run, first set parameters in the SETTINGS section.
QUERY
Once paramaters are set, click EXECUTE to send ramping command to ami
The STOP command will ramp down to zero at 0.5 A/min.
Please only set one ramp rate at a time, either up or down.
To change ramp rate, first PAUSE the current ramping function and then start again.
The Status command queries the AMI

'''

rU = False
#rD = False
running = False
dIdt = 0
L = 16

ami = serial.Serial('COM6', 115200, rtscts=1)
ami.write('SYSTem:LOCal\n')

def stop():
	#ramp down current to zero at 0.5 A/min.
	global running
	running = False
	ami.write('CONF:CURR:TARG 0\n')
	ami.write('CONF:RAMP:RATE:CURR 1,0.50,10\n')
	ami.write('RAMP\n')
	print 'Powering Down'
def status():
	try:
		#send querying code to AMI (111 is sum of binary inputs)
		ami.write('*ETE 111\n')
		ami.write('*TRG\n')
		trg = ami.readline()
		print trg

		ami.write('RAMP:RATE:UNITS?\n')
		unit = ami.readline()
		unit=int(unit)
		if unit == 0:
			print 'Ramp rate is in seconds'
			print 'DO NOT PROCEED'
		if unit == 1:
			print 'Ramp rate is in minutes'

		ami.write('STATE?\n')
		state = ami.readline()
		state = int(state)
		if state == 1:
			print 'RAMPING to target current'
		elif state == 2:
			print 'HOLDING at the target current'
		elif state == 3:
			print 'PAUSED'
		elif state == 4:
			print 'Ramping in MANUAL UP mode'
		elif state == 5:
			print 'Ramping in MANUAL DOWN mode'
		elif state == 6:
			print 'ZEROING CURRENT'
		elif state == 7:
			print 'Quench Detected'
		elif state == 8:
			print 'At ZERO current'
		elif state == 9:
			print 'Heating persistent switch'
		elif state == 10:
			print 'Cooling persistent switch'
		else:
			print 'State = 0'


		ami.write('VOLT:LIM?\n')
		vLim = ami.readline()
		print 'Voltage Limit: '
		print vLim

		ami.write('CURR:TARG?\n')
		targ = ami.readline()
		print 'Target: '
		print targ

		ami.write('RAMP:RATE:CURR:1?\n')
		rrCur = ami.readline()
		print 'Current Ramp Up Rate, Upper Bound: '
		print rrCur
		'''
		ami.write('RAMPD:ENAB?\n')
		enab = ami.readline()
		print enab
		ami.write('RAMPD:RATE:CURR:1?\n')
		rdCur = ami.readline()
		print 'Current Ramp Down Rate: '
		print rdCur
		'''
	except:
		print 'Unable to query AMI, do not proceed'
def start():
	global running
	ami.write('RAMP:RATE:UNITS?\n')
	unit = ami.readline()
	unit = int(unit)
	print unit
	if check()==True and unit==1: 
		#if unit==1:
		#make sure A/min
		running = True
		print 'Starting ADR'
		#if ramp up was set
		if rU and trgt == True:
			ami.write('RAMP\n')
			print 'Ramping to ' + str(target) + ' I at ' + str(dIdt) + ' A/min.'
			while running:
				check()
			
		else:
			print 'Error: Please set Target and Ramprate'
	else:
		print 'Check units and temperture'

def pause():
	global running
	if running == False:
		running= True
		print 'Resuming'
		start()
	else:
		running = False
		print 'Pausing..'
		ami.write('PAUSE\n')
		#rU = False
		

def setV(self):
	#set max Voltage
	volt = self.volt.get()
	volt = str(volt)
	vCommand = 'CONF:VOLT:LIM '+volt+'\n'
	ami.write(vCommand)
	print 'Max Voltage set at: ' + volt + ' V'


def setI(self):
	#set max Current
	current = self.current.get()
	if current > 10:
		print 'Max current must be <= 10A'
	else:
		iCommand = 'CONF:CURR:LIM '+str(current)+'\n'
		ami.write(iCommand)
		print 'Max current set at: ' + current + ' A'

def setUp(self):
	#set increasing ramp rate
	#global dIdt
	dIdt = self.rampup.get()
	
	global rU
	#global upCommand
	rU = True
	#global rD
	#rD = False
	print 'Ramp rate set at: ' + dIdt + ' A/min.'
	#dIdt = float(dIdt)/60
	upCommand = 'CONF:RAMP:RATE:CURR 1,'+str(dIdt)+',10\n'
	#print upCommand
	ami.write(upCommand)


def setTarget(self):
	#set target current
	global target
	global trgt
	global targCommand
	trgt = True
	target = self.target.get()
	print 'Target I set at: ' + target + ' A'
	targCommand = 'CONF:CURR:TARG '+str(target)+'\n'
	ami.write(targCommand)

def check():
	#check cryostat temperatures and mag resistance
	try:
		temps = get_temps()
		
		print 'ADR T:'
		print temps[18]
		#get ramp rate
		dIdt = rampRate()
		time.sleep(1)
		ami.write('VOLT:SUPP?\n')
		volt = ami.readline()
		volt = float(volt)
		print 'V: '
		print volt
		ami.write('CURR:MAG?\n')
		curr = ami.readline()
		curr = float(curr)
		print 'I:'
		print curr
		#print 'place'
		#ami.write('IND?\n')
		#L = ami.readline()
		#print 'dIdt: '
		#print dIdt
		#calculate resistance
		if curr > 0.05 and dIdt!=0 and volt > 0.05:
			Z = (volt-dIdt*L)/curr
		else: 
			Z=0
		print 'Z:'
		print Z
		#4k HTS
		if temps[1] > 8:
			Alarm+1
			alarm()
		if temps[1] > 8.5:
			print '4K HTS too hot'
			stop()
			return False
		#4k Plate
		if temps[15] > 5:
			alarm()
		if temps[15] > 6:
			print '4K Plate too hot'
			stop()
			return False
		#50k HTS
		if temps[2] > 61:
			alarm()
		if temps[2] > 70:
			print '50K too hot'
			stop()
			return False


		#check magnet resistance
		if Z >= 0.025:
			print 'resistance too high'
			stop()
			return False
		else:
			return True
	except Exception as e:
		print 'Error Occured:'
		print e
		stop()
		return False


def rampRate():

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
'''
	if running:
		ami.write('RAMP:RATE:CURR: 1?\n')
		strng = ami.readline()
		a = strng.split(',')
		#print a
		rate = float(a[0])/60

	else:
		rate = 0
	#print rate
	return rate
'''
def execute():
	new_thread = threading.Thread(target = start)
	new_thread.start()

class App:
	#run = False
	#temp = '1'
	def __init__(self):
		self.master = Tk()
		self.master.title('ADR Controller')
		self.volt = StringVar()
		self.current = StringVar()
		self.rampup = StringVar()
		self.rampdown = StringVar()
		self.target = StringVar()

		self.label0 = Label(self.master, text='COMMAND', font=('Impact', 10))
		self.label0.grid(row=0, column=0, pady=10, padx=10)
		self.label1 = Label(self.master, text='SETTINGS', font=('Impact', 10))
		self.label1.grid(row=2, column=0, pady=10, padx=10)

		self.button1 = Button(self.master,text='Pause', command = pause, activebackground = 'purple')
		self.button1.grid(row=1,column=3)

		self.button2 = Button(self.master,text= 'STOP', command = stop, activebackground = 'purple')
		self.button2.grid(row=1,column=2)

		self.button3 = Button(self.master,text= 'Status', command = status, activebackground = 'purple')
		self.button3.grid(row=1,column=0)

		self.button4 = Button(self.master,text= 'EXECUTE', command = execute, activebackground = 'purple')
		self.button4.grid(row=1,column=1)

		self.button5 = Button(self.master,text= 'Set Max V', command = lambda: setV(self), activebackground = 'purple')
		self.button5.grid(row=4,column=0)

		self.button6 = Button(self.master,text= 'Set Max I', command = lambda: setI(self), activebackground = 'purple')
		self.button6.grid(row=4,column=1)

		self.button7 = Button(self.master,text= 'Set RampRate', command = lambda: setUp(self), activebackground = 'purple')
		self.button7.grid(row=4,column=2)

		#self.button8 = Button(self.master,text= 'Set Ramp Down', command = lambda: setDown(self), activebackground = 'purple')
		#self.button8.grid(row=4,column=3)

		self.button9 = Button(self.master,text= 'Set Target', command = lambda: setTarget(self), activebackground = 'purple')
		self.button9.grid(row=4,column=4)

		self.myentry1 = Entry(self.master, textvariable=self.volt)
		self.myentry1.grid(row=3, column=0)

		self.myentry2 = Entry(self.master, textvariable=self.current)
		self.myentry2.grid(row=3, column=1)

		self.myentry3 = Entry(self.master, textvariable=self.rampup)
		self.myentry3.grid(row=3, column=2)

		#self.myentry4 = Entry(self.master, textvariable=self.rampdown)
		#self.myentry4.grid(row=3, column=3)

		self.myentry5 = Entry(self.master, textvariable=self.target)
		self.myentry5.grid(row=3, column=4)
		#self.myentry.insert(END, 'Type Temp Here')

		#self.counter = 0
		self.master.mainloop()


App()
#main()
ami.close()
