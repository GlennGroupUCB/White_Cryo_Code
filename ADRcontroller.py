import visa
import serial
import time
from functions import get_temps
from Tkinter import *

#Created by Tim Childers 17/07/2017
#TO DO:

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
rD = False
running = False
dIdt = 0

ami = serial.Serial('ami', 115200, rtscts=1)

def stop():
    #ramp down current to zero at 0.5 A/min.
    global running
    running = False
    ami.write('CONF:RAMPD:RATE:CURR 1,0.50,0\n')
    ami.write('RAMP\n')
    print 'Powering Down'
def status():
    try:
        #send querying code to AMI (111 is sum of binary inputs)
        ami.write('*ETE 111\n')
        #trigger to send output
        ami.write('*TRG\n')
        trg = ami.readline()
        print trg

        ami.write('RAMP:RATE:UNITS?\n')
        unit = ami.readline()
        if unit == 0:
            print 'Ramp rate is in seconds'
            print 'DO NOT PROCEED'
        if unit == 1:
            print 'Ramp rate is in minutes'

        ami.write('STATE?')
        state = ami.readline()
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
        print 'Current Ramp Up Rate: '
        print rrCur
        ami.write('RAMPD:RATE:CURR:1?\n')
        rdCur = ami.readline()
        print 'Current Ramp Down Rate: '
        print rdCur

    except:
        print 'Unable to query AMI, do not proceed'
def start():
    global running
    '''
    if running:
        running = False
    '''
    ami.write('RAMP:RATE:UNITS?\n')
    unit = ami.readline()


    if check()==True and unit ==1: #make sure A/min
        running = True
        print 'Starting ADR'
        #if ramp up was set
        if rU == True:
            upCommand = 'CONF:RAMP:RATE:CURR 1,'+dIdt+','+target
            #print upCommand
            ami.write(upCommand)
            ami.write('RAMP\n')
            print 'Ramping to ' + target + ' I at ' + dIdt + ' A/min.'
            while running:
                check()
                time.sleep(1)
        #if ramp down was selected
        elif rD == True:
            print 'Ramping to ' + target + ' I at ' + dIdt + ' A/min.'
            downCommand = 'CONF:RAMP:RATE:CURR 1,'+dIdt+','+target
            #print downCommand
            ami.write(downCommand)
            ami.write('RAMP\n')
            while running:
                check()
                time.sleep(1)
        else:
            print 'Error: Please Check Settings'

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
        rU = False
        rD = False

def setV(self):
    #set max Voltage
    volt = self.volt.get()
    vCommand = 'CONF:VOLT:LIM '+volt
    ami.write(vCommand)
    print 'Max Voltage set at: ' + volt + ' V'


def setI(self):
    #set max Current
    current = self.current.get()
    iCommand = 'CONF:CURR:LIM '+current
    ami.write(iCommand)
    print 'Max current set at: ' + current + ' A'

def setUp(self):
    #set increasing ramp rate
    global dIdt
    dIdt = self.rampup.get()
    global rU
    rU = True
    global rD
    rD = False
    print 'Ramp rate set at: ' + dIdt + ' A/min.'
    dIdt = float(dIdt)/60

def setDown(self):
    #set decreasing ramp rate
    global dIdt
    dIdt = self.rampdown.get()
    global rU
    rU = False
    global rD
    rD = True
    print 'Ramp rate set at: -' + dIdt + ' A/min.'
    dIdt = float(dIdt)/60

def setTarget(self):
    #set target current
    global target
    target = self.target.get()
    print 'Target I set at: ' + target + ' A'

def check():
    #check cryostat temperatures and mag resistance
    try:
        temps = get_temps()
        ami.write('VOLT:MAG?\n')
        volt = ami.readline()
        ami.write('CURR:MAG?\n')
        curr = ami.readline()
        #ami.write('IND?\n')
        #L = ami.readline()
        #get ramp rate
        dIdt = rampRate()
        #calculate resistance
        Z = (volt-dIdt*L)/curr

        #4k HTS
        if temps[1] > 8:
            Alarm+1
            alarm()
        if temps[1] > 8.5:
            stop()
            return False
        #4k Plate
        if temps[15] > 5:
            alarm()
        if temps[15] > 6:
            stop()
            return False
        #50k HTS
        if temps[2] > 61:
            alarm()
        if temps[2] > 70:
            stop()
            return False


        #check magnet resistance
        if Z >= 0.025:
            stop()
            return False
        else:
            return True
    except:
        print 'Error Occured'
        stop()
        return False


def rampRate():

    if rU:
        ami.write('RAMP:RATE:CURR: 1?\n')
        strng = ami.readline()
        a = strng.split(',')
        rate = float(a[0])/60
    elif rD:
        ami.write('RAMPD:RATE:CURR: 1?\n')
        strng = ami.readline()
        a = strng.split(',')
        rate = float(a[0])/60
    else:
        rate = 0
    return rate

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

        self.button4 = Button(self.master,text= 'EXECUTE', command = start, activebackground = 'purple')
        self.button4.grid(row=1,column=1)

        self.button5 = Button(self.master,text= 'Set Max V', command = lambda: setV(self), activebackground = 'purple')
        self.button5.grid(row=4,column=0)

        self.button6 = Button(self.master,text= 'Set Max I', command = lambda: setI(self), activebackground = 'purple')
        self.button6.grid(row=4,column=1)

        self.button7 = Button(self.master,text= 'Set Ramp Up', command = lambda: setUp(self), activebackground = 'purple')
        self.button7.grid(row=4,column=2)

        self.button8 = Button(self.master,text= 'Set Ramp Down', command = lambda: setDown(self), activebackground = 'purple')
        self.button8.grid(row=4,column=3)

        self.button9 = Button(self.master,text= 'Set Target', command = lambda: setTarget(self), activebackground = 'purple')
        self.button9.grid(row=4,column=4)

        self.myentry1 = Entry(self.master, textvariable=self.volt)
        self.myentry1.grid(row=3, column=0)

        self.myentry2 = Entry(self.master, textvariable=self.current)
        self.myentry2.grid(row=3, column=1)

        self.myentry3 = Entry(self.master, textvariable=self.rampup)
        self.myentry3.grid(row=3, column=2)

        self.myentry4 = Entry(self.master, textvariable=self.rampdown)
        self.myentry4.grid(row=3, column=3)

        self.myentry5 = Entry(self.master, textvariable=self.target)
        self.myentry5.grid(row=3, column=4)
        #self.myentry.insert(END, 'Type Temp Here')

        #self.counter = 0
        self.master.mainloop()


App()
#main()
#ami.close()
