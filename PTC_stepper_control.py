#!/usr/bin/env python
#Control the stepper motor of the pulse tube cooler with an external 
#linear driver by Precision Motion Control (PMC)

import sys
import serial

#Define the serial port to use, use udev rules to create a static address
port = 'COM5'

#Define min and max frrequencies to run the PTC in Hz
fmin = 0.1
fmax = 2.0

def turn_on_1p4Hz():
    #This is the factory default frequency
    ser = serial.Serial(port) #Open motor serial port
    ser.write('MC H+ A70 V70 G ')
    ser.close()
    return

def turn_on(velocity):
    #Select a particular frequency
    ser = serial.Serial(port) #Open motor serial port
    cmd = 'MC H+ A70 V'+str(int(velocity))+' G '
    print 'Sending start command',cmd
    ser.write(cmd)
    ser.close()
    return

def turn_off():
    ser = serial.Serial(port) #Open motor serial port
    print 'Sending command current off'
    ser.write('CF ')
    print 'Sending stop command'
    ser.write('S ')
    ser.close()
    return

if __name__=='__main__':
    if len(sys.argv) < 2:
        print 'Provide a frequency between '+str(fmin)+' and '+str(fmax)+' Hz'
        print 'Zero frequency will turn motor off'
        sys.exit()
    frequency = float(sys.argv[1])
    #A factor of 50 translate between Hz and motor velocity
    velocity = int(frequency * 50)
    if frequency == 0:
        print 'You have selected to turn the motor off'
        raw_input('Do you want to continue?')
        turn_off()
        sys.exit()        
    elif (frequency > fmin) and (frequency <= fmax):
        print 'You have selected',frequency,'Hz, corresponding to velocity of',velocity
        raw_input('Do you want to continue?')
        turn_on(velocity)
        sys.exit()
    else:
        print 'You have selected a frequency',frequency,'. That is out of range.'
        print 'Provide a frequency between '+str(fmin)+' and '+str(fmx)+' Hz'
        print 'Zero frequency will turn motor off'
        print 'If you wish to select this frequency, modify the code'
        sys.exit()

