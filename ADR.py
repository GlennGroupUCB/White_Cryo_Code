import visa
import serial
import time
from functions import get_temps
import csv
import threading
from Tkinter import *

#written by Tim Childers to run ADR cooling script 18/07/2017

#To Do:
#calibrate ramp rates
#Keep Inductance constant?
#double check safegaurds
#ramp down stages


'''
READ ME:
This script is written to be run with fridge_cycle_ADRoff.py and the ADR switch off.
It follows Addi's recipe for cooling the ADR down. To run the script using the GUI:
1) Set the desired temperature you want the ADR to run at. (This can be changed while running the code.)
2) Hit Start to begin the script. The ADR switch will be powered at 1.5V until the He-4 and He-3 heads
   equilibrate below 1.1K. It then shuts off the switch and begins the ramping cycle. The ramping cycle
   is controlled by continous runs of the check() function which monitors temp and resistance. It will
   alert the Alarm() and stop() functions if wrong conditions are met.
   The temperature of the ADR is controlled by varying rates of applied current based on distance from
   the desired temp. *These numbers will have to be tweaked later for better results.
'''

Alarm = 0
count = 0
temp = 0
L = 16 #magnet Inductance
#rampState = 'Off'
running = True
first = True
count=0
t=0
#open connection to ADR switch power supply
ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3647 on top row of rack
ag49.write('OUTPut ON')
ami = serial.Serial('ami', 115200, rtscts=1)
#should I add a timeout?

#Initialize writing to file
now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
file_prefix =  "/home/timotheous/White_Cryo_Code/ADR/" + date_str
#file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/ADR/" + date_str
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
    ami = serial.Serial('ami', 115200, rtscts=1)
    #ami.write('SYST:REM\n')

    #Returns '0' for ramp rates displayed/specified in terms of seconds, or '1' for minutes.
    ami.write('RAMP:RATE:UNITS?\n')
    unit = ami.readline()
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
            print 'Error'

    else:
        print 'Please set units to A/min.'



def switchOn():
    global running
    global count
    while running:
        #keep ADR switch on until desired conditions
        try:
            temps = get_temps()
            if temp[17] < 1.2 and count == 0:
                #if He4 is below 1.2K turn on ADR switch
                ag49.write('INST:SEL OUT1')
                ag49.write('Volt 1.5')
                #3.5 #Afyhrie changed from 1.75 to 1.5 on June 28 2017
                #to make sure the ADR switch doesn't heat above 17 K
                print 'ADR switch ON'
                count=1
            if temp[12] > 10 and count == 1:
                #wait till switch heats up to signal next step
                count=2
            if temps[16] and temps[17] < 1.1 and count == 2:
                #wait till He3/4 return to normal temp. before switch
                #temps[16] and temps[17] < 1.1. ?????
                print 'He3/He4 Heads Stabalized'
                count=3
                break
            if temps[12] > 17:
                print 'ADR switch above 17K'
                switchOff()
                running = False
                break
        except:
            #if get_temps fails, turn off ADR switch to prevent overheating
            switchOff()
            break
def switchOff():
    #turn off ADR switch
    ag49.write('INST:SEL OUT1')
    ag49.write('Volt 0')
    print 'ADR switch OFF'

def rampU():
    #begin increasing ramp rate
    global rampState
    global count
    rampState = 'U'

    if check(rampState) == True and running:
        #set initial ramp rate to 0.5 A/min to 10A target
        ami.write('CONF:RAMP:RATE:CURR 1,0.5,10\n')
        count=4
        print 'Ramping to 10A at 0.5 A/min'
        #infite loop b/c check becomes driver function
        while check(rampState) == True and running:
            pass
    else:
        print 'Check Temperatures or Resistance'

def rampD():
    global rampState
    global count
    rampState = 'D'
    #ramp down to 1.5A at 0.25 A/min
    ami.write('CONF:RAMPD:RATE:CURR 1,0.25,1.5\n')
    count=7
    print 'Ramping to 1.5A at -0.25 A/min.'
    #try:
    while check(rampState)==True and running:
        temps = get_temps()
            #Ramp down to zero at varying rates based on target temp
            #temp must be converted to float each time b/c Tkinter is not thread-safe
        if  temps[18] > float(temp) + 0.1 :
            ami.write('CONF:RAMPD:RATE:CURR 2,0.25,0.75\n')
        elif float(temp)+0.1 > temps[18] >= float(temp) + 0.05:
            ami.write('CONF:RAMPD:RATE:CURR 2,0.25,0\n')
        elif float(temp)+ 0.05 > temps[18] >= float(temp) + 0.01:
            ami.write('CONF:RAMPD:RATE:CURR 2,0.1,0\n')
        elif float(temp)+0.01 > temps[18] >= float(temp) + 0.005:
            ami.write('CONF:RAMPD:RATE:CURR 2,0.01,0\n')
        elif float(temp)+0.005 > temps[18] >= float(temp) + 0.001:
            ami.write('CONF:RAMPD:RATE:CURR 2,0.005,0\n')
        elif float(temp)+0.001 > temps[18] >= float(temp) + 0.0005:
            ami.write('CONF:RAMPD:RATE:CURR 2,0.001,0\n')
        elif float(temp)+0.0005 > temps[18] >= float(temp) + 0.0001:
            ami.write('CONF:RAMPD:RATE:CURR 2,0.0005,0\n')
        else:
            ami.write('PAUSE\n')
            time.sleep(1)
    #except:
    #        stop()
    #        print 'Error Occured'

def check(rampState):
    #check cryostat temperatures and mag resistance
    #also driver function for ramping
    global count
    global t
    try:
        t = time.time() - t0
        temps = get_temps()
        ami.write('VOLT:MAG?\n')
        volt = ami.readline()
        ami.write('CURR:MAG?\n')
        curr = ami.readline()
        #ami.write('IND?\n')
        #L = ami.readline()
        #get ramp rate
        dIdt = rampRate(rampState)
        #calculate resistance
        Z = (volt-dIdt*L)/curr
        #write to file
        writeToFile(volt,curr,L,dIdt,Z)
        #4k HTS
        if temps[1] > 8:
            Alarm+1
            alarm()
        if temps[1] > 8.5:
            stop()
        #4k Plate
        if temps[15] > 5:
            alarm()
        if temps[15] > 6:
            stop()
        #50k HTS
        if temps[2] > 61:
            alarm()
        if temps[2] > 70:
            stop()
        #turn off ADR switch if He-4 Head and ADR cool to 1.2K, wait 5 minutes from start of ramping
        #wait because initially temperature will be low before switch
        #Does the ADR heat up He3/4 initially when ramping?
        if temps[16] and temps[17] < 1.2 and t>5.0*60.0 and count==4:
            count=5
            switchOff()

        #ADR Switch temp and begin ramp down
        if temps[12] < 3.8 and count == 5:
            count=6
            rampD()
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

def rampRate(ramp):
    if ramp == 'U':
        ami.write('RAMP:RATE:CURR: 1?\n')
        strng = ami.readline()
        a = strng.split(',')
        rate = float(a[0])/60
    elif ramp == 'D':
        ami.wrte('RAMPD:RATE:CURR: 1?\n')
        strng = ami.readline()
        a = strng.split(',')
        rate = float(a[0])/60
    else:
        rate = 0
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
    print 'The temperature is set at: ' + temp + 'K'
    #return temp
def stop():
    #ramp down current to zero at 0.5 A/min.
    global running
    running = False
    ami.write('CONF:RAMPD:RATE:CURR 1,0.50,0\n')
    print 'Powering Down to 0A at -0.5 A/min.'
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
    ami.write('STATE?\n')
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
    ami.write('RAMP:RATE:CURR:1\n')
    print 'Current Ramp Up Rate: '
    currRampRate = ami.readline()
    print currRampRate
    ami.write('RAMPD:RATE:CURR:1\n')
    currRampDown = ami.readline()
    print 'Current Ramp Down Rate: '
    print currRampDown
    print 'Target Temperature: '+temp+'K'

def writeToFile(volt,curr,L,dIdt,Z,y):
    global first
    #print 'Writing to file... '
    now = datetime.datetime.now()
    if first: #if it is the first time writing to file put in a header
        writer.writerow(['Date-LocalTime', 'Voltage(V)', 'Current(A)', 'Inductance(H)', 'dI/dt', 'Resistance(Ohms)', 'ADR temp'])

    writer.writerow([now,volt,curr,L,dIdt,Z,y[18]])
    first = False





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

        self.button4 = Button(self.master,text= 'Pause Ramp', command = pause, activebackground = 'purple')
        self.button4.grid(row=4,column=1)

        self.button5 = Button(self.master,text= 'Status', command = status, activebackground = 'purple')
        self.button5.grid(row=4,column=1)

        self.myentry = Entry(self.master, textvariable=self.temp)
        self.myentry.grid(row=1, column=0)
        #self.myentry.insert(END, 'Type Temp Here')

        #self.counter = 0
        self.master.mainloop()


App()
#main()
ami.close()
csvfile.close()
