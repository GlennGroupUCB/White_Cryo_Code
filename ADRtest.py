import csv
import time
import datetime
import os
import sys
import random
import threading
#import subprocess as sp
import numpy as np
#import functions
from Tkinter import *

#written by Tim Childers to test functionality of ADR.py 18/07/2017

Alarm = 0
count = 0
temp = 0.0
volt = 0.001
curr = 0.001
L = 16.0
dLdT = 0.008333
ag49 = False
running = True
paused = False
first = True
targ = False
t=0

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

y = []
for i in range(19):
    y.append(0)
y[1]=4.000
y[2]=49.000
y[12]=4.000
y[15]=4.000
y[16]=1.500 #He3
y[17]=3.900 #He4
y[18]=2.900

def main():
    try:
        global t0

        #turn on ADR Switch
        if count == 0:
            switchOn()

        t0 = time.time()
        #begin ramp up
        if targ == True:
            rampU()

    except KeyboardInterrupt:
        pass

def switchOn():
    #ag49.write('INST:SEL OUT1')
    #ag49.write('Volt 1.5')#3.5 #Afyhrie changed from 1.75 to 1.5 on June 28 2017
    #to make sure the ADR switch doesn't heat above 17 K
    global running
    global count
    i=1
    while running:
        #try:
        #temps = functions.get_temps()
        temps = get_temps()
        decT(i)
        if temps[17] < 1.2 and count == 0:
            #turn on ADR switch
            #ag49.write('INST:SEL OUT1')
            #ag49.write('Volt 1.5')
            print 'ADR switch ON'
            count = 1 #1
            i = 2
        if temps[12] > 10 and count == 1:
            count = 2 #2
            i = 2
        if temps[16] and temps[17] < 1.1 and count == 2:
            print 'He3/He4 Heads Stabalized'
            count = 3 #3
            i = 2
            break
        if temps[12] > 17:
            print 'ADR above 17K'
            switchOff()
            running = False
            break
        #except:
        #    print 'here'
        #    switchOff()
        #    break
def get_temps():

    print 'He3 = '+str(y[16])
    print 'He4 = '+str(y[17])
    print 'ADR = '+str(y[18])
    print 'ADR switch = '+str(y[12])

    time.sleep(1)
    return y

def decT(stage):
    global y
    if stage == 1 and paused == False:
        y[16] = y[16]-0.01
        y[17] = y[17]-0.1
        #y[12] = y[12]+0.2
        print 'stage 1'
    elif stage == 2 and paused == False:
        y[16] = y[16]-0.005
        y[17] = y[17]-0.001
        y[12] = y[12]+0.1
        print 'stage 2'
    elif stage == 3 and paused == False:
        y[16] = y[16]-0.005
        y[17] = y[17]-0.001
        y[12] = y[12]-0.1
        print 'stage 3'
        #time.sleep(1)
    elif stage == 4 and paused == False:
        y[18] = y[18]-0.1
        print 'stage 4'
        #time.sleep(1)
    elif stage == 5 and paused == False:
        y[18] = y[18]-0.05
        print 'stage 5'
        #time.sleep(1)
    elif stage == 6 and paused == False:
        y[18] = y[18]-0.01
        print 'stage 6'
        #time.sleep(1)
    elif stage == 7 and paused == False:
        y[18] = y[18]-0.005
        print 'stage 7'
        #time.sleep(1)
    elif stage == 8 and paused == False:
        y[18] = y[18]-0.001
        print 'stage 8'
        #time.sleep(1)
    elif stage == 9 and paused == False:
        print 'stage 9'
        y[18] = y[18]-0.0005
        #time.sleep(1)
    else:
        print 'Paused'

def switchOff():
    #ag49.write('INST:SEL OUT1')
    #ag49.write('Volt 0')

    print 'ADR switch OFF'

def rampU():
    global count
    global curr
    global volt
    print 'Ramping Up'
    if check() == True and running:
        #ami.write('CONF:RAMP:RATE:CURR 1,0.5,10')
        curr = 10
        volt = 0.1
        count = 4 #4
        while check() == True and running:
            decT(3)
            pass
    else:
        print 'check temperatures or resistance'

def rampD():
    #ramp down to 1.5A at 0.25 A/min
    #ami.write('CONF:RAMPD:RATE:CURR 1,0.25,1.5')
    global curr
    global volt
    global temp
    global dIdt
    global count

    print 'Ramping down'
    curr = 1.5
    volt = 0.16
    count = 7

    while check()==True and running:
        try:
            #ramp down to zero at varying rates based on target temp
            temps = get_temps()


            if  temps[18] > float(temp) + 0.100:
                decT(4)
                #defining as float b/c Tkinter isn't thread protected and redefines as str
            #elif temps[18] >= temp + 0.05 and temps[18]< temp+0.1:
            elif float(temp)+0.1 > temps[18] >= float(temp)+0.05:
                #ami.write('CONF:RAMPD:RATE:CURR 2,0.25,0')
                decT(5)
                print 'rate = 0.25'
                dIdt = 0.25/60
            #elif temps[18] >= temp + 0.01 and temps[18]<temp+0.05:
            elif float(temp)+0.05 > temps[18] >= float(temp) + 0.01:
                #ami.write('CONF:RAMPD:RATE:CURR 2,0.1,0')
                decT(6)
                print 'rate = 0.01'
                dIdt = 0.01/60
            #elif temps[18] >= temp + 0.005 and temps[18]<temp+0.01:
            elif float(temp)+0.01 > temps[18] >= float(temp) + 0.005:
                #ami.write('CONF:RAMPD:RATE:CURR 2,0.01,0')
                decT(7)
                print 'rate = 0.005'
                dIdt = 0.005/60
            #elif temps[18] >= temp + 0.001 and temps[18]<temp+0.005:
            elif float(temp)+0.005 > temps[18] >= float(temp) + 0.001:
                #ami.write('CONF:RAMPD:RATE:CURR 2,0.01,0')
                decT(8)
                print 'rate = 0.001'
                dIdt = 0.001/60
            #elif temps[18] >= temp + 0.0005 and temps[18]<temp+0.001:
            elif float(temp)+0.001 > temps[18] >= float(temp) + 0.0005:
                #ami.write('CONF:RAMPD:RATE:CURR 2,0.001,0')
                decT(9)
                print 'rate = 0.0005'
                dIdt = 0.0005/60
            else:
                print 'Wait'
                time.sleep(1)
        except:
            pass


def check():
    #check cryostat temperature
    global count
    global Alarm
    global t
    print 'Checking...'
    temps = get_temps()
    t = time.time() - t0
    z = (volt-dLdT*L)/curr
    writeToFile(temps,t,z)

    #4k HTS
    if temps[1] > 8:
        Alarm+1
        alarm()
    if temps[1] > 8.5:
        stop()
    #4k Plate
    if temps[15] > 5:
        Alarm+1
        alarm()
    if temps[15] > 6:
        stop()
    #50k HTS
    if temps[2] > 61:
        Alarm+1
        alarm()
    if temps[2] > 70:
        stop()
    #turn off ADR switch if He-4 Head and ADR cool to 1.2K, wait 5 minutes from start of ramping
    if temps[16] and temps[17] < 1.1 and t>0.5*60 and count==4:
        count=5 #5
        switchOff()

    #ADR Temp and begin ramp down
    if temps[12] < 3.8 and count==5:
        count=6
        rampD()
        return False

    #check AMI resistance
    #volt = ami.write('VOLT:MAG?')
    #curr = ami.write('CURR:MAG?')
    if z >= 0.025:
        print 'Resistance too high'
        stop()
        return False
    else:
        return True
def stop():
    #ramp down current to zero
    global running
    running = False
    print 'Powering Down'
def alarm():
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
    global targ
    temp = self.temp.get()
    print 'The temperature is set at: ' + temp + 'K'
    targ = True

def writeToFile(y,t,z):
    global first
    now = datetime.datetime.now()
    print 'Writing to file... '
    if first: #if it is the first time writing to file put in a header
        writer.writerow(['Human readable time', 'Voltage(V)', 'Current(A)', 'Resistance(Ohms)','ADR temp'])

    writer.writerow([now,volt,curr,z,y[18]])
    first = False

def pause():
    global running
    print 'COUNT = ' + str(count)
    if running:
        running = False
        print 'Paused'
    elif running == False:
        running = True
        start()
        print 'Resuming..'

    #ami.write('PAUSE')

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
    #ami.write('STATE?')
    #state = ami.readline()
    state = random.randrange(10)
    if state == 1:
        print 'RAMPING to target current'
    if state == 2:
        print 'HOLDING at the targe current'
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
    #ami.write('*ETE 111\n')
    #ami.write('*TRG\n')
    #ami.readline()

    #ami.write('VOLT:LIM?\n')
    print 'Voltage Limit: '
    #ami.readline()
    #ami.write('CURR:TARG?\n')
    print 'Target: '
    #ami.readline()
    #ami.write('RAMP:RATE:CURR:1\n')
    print 'Current Ramp Up Rate: '
    #ami.readline()
    #ami.write('RAMPD:RATE:CURR:1\n')
    #ami.readline()
    print 'Current Ramp Down Rate: '


class App:
    #run = False
    #temp = '1'
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
        self.button2.grid(row=4,column=3)

        self.button3 = Button(self.master,text= 'Start Ramp', command = start, activebackground = 'purple')
        self.button3.grid(row=4,column=0)

        self.button4 = Button(self.master,text= 'Pause Ramp', command = pause, activebackground = 'purple')
        self.button4.grid(row=4,column=2)

        self.button5 = Button(self.master,text= 'Status', command = status, activebackground = 'purple')
        self.button5.grid(row=4,column=1)

        self.myentry = Entry(self.master, textvariable=self.temp)
        self.myentry.grid(row=1, column=0)
        #self.myentry.insert(END, 'Type Temp Here')

        #self.counter = 0

        self.master.mainloop()


App()
csvfile.close()
