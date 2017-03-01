# -*- coding: utf-8 -*-
"""
Created on Tue Aug 09 13:55:21 2016
Important links:
VRO-1 User manual - http://www.velmex.com/Downloads/User_Manuals/VRO%20Reference%20Manual.pdf
VXM-1 User manual - http://www.velmex.com/Downloads/User_Manuals/vxm_user_manl.pdf

@author: Mike
"""

# Modules
import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
import numpy as np

# Settings
speed = 1 # cm/s, max speed is 20 rev/sec, 8000 step/s, 2 in/sec, 5.08 cm/s
timeout = 0.03 # Arbitrary timeout stops VRO-1 serial read

# Stepper motor info
stepPerRev = 400 # Vexta pk-266-03B-P2 stepper, 1.8 degrees/step but somehow 400 step/rev
inPerRev = 0.1 # lead of lead screw
cmPerRev = inPerRev * 2.54 
revPerSec = speed / cmPerRev
stepPerSec = stepPerRev * revPerSec

# Variables and empty lists
timeList = []
positionListRaw = []

throw = 101.6 # cm, One way travel distance of Velmex BiSlide
dTrav = throw * 2 # Total distance traveled by flat mirror
scanTime = dTrav / speed # Time to complete motion
nLoop = scanTime / (timeout + 0.02) + (0.2 * scanTime / (timeout + 0.02)) # Number of loops (Samples?)

# Find, Identify and Configure serial ports (VXM-1 controller, VRO-1 encoder, DAC)
ports = list(serial.tools.list_ports.comports())
for i in range(0, len(ports)):
    ser = serial.Serial(ports[i][0], timeout = 5)
    ser.write('V')
    res = ser.readline()
    ser.close()
    
    if res == 'B' or res == 'R' or res == 'J':
        serCon = serial.Serial(ports[i][0])
        
    elif res == 'P':
        serEnc = serial.Serial(ports[i][0], timeout = timeout)
        serEnc.write('@')
        
    elif res == 'S':
        serEnc = serial.Serial(ports[i][0], timeout = timeout)
        serEnc.write('Q')
        
    elif res == 'F' or res == 'D':
        serEnc = serial.Serial(ports[i][0], timeout = timeout)
        
    else:
        print 'Error: Check serial ports'


#serDAC = serial.Serial('COM1')

# Put VRO-1 in display mode
serEnc.write('@')

# VXM-1 Send flat to start, negative limit switch (closest position to motor and beamsplitter in 8/5 FTS config)
serCon.write('F,C,I1M-0,R,')

# VRO-1 Read home encoder position - Maybe unnecessary see line 58 
serEnc.write('X')
home = serEnc.readline()

# Start time for scan
startTimeRaw = time.time()
startTime = startTimeRaw - startTimeRaw

# Speed limit 
if stepPerSec > 8000:
    print 'Error: Max speed, 8000 rev/s, exceeded. Change speed.' #python 2.7
    
    # Close serial ports for rerun
    serCon.close()
    serEnc.close()

# Begin loop for time and encoder data acq
else:
    for i in range(0,int(nLoop)):

        serEnc.write('X')
        
        position = serEnc.readline()
        timeList.append(time.time())
        positionListRaw.append(position)
        
        if i == 20:
            serCon.write('F,C,S1M' + str(int(stepPerSec)) + ',I1M0,I1M-0,R,')

    positionListRaw.insert(0, home)
    positionList = map(str.strip, positionListRaw)
    positionList = [float(i) for i in positionList]
    positionArray = np.asarray(positionList)
    timeList.insert(0, startTimeRaw)
    timeArray = np.asarray(timeList) - startTimeRaw
    
#home = positionArray[0]    
    
print timeArray
print positionArray

plt.plot(timeArray,positionArray)
plt.show()

serEnc.write('X')
end = serEnc.readline()

if abs(float(home) - float(end)) > 0.0004:
    print 'Warning: Home and end position difference greater then known uncertainty of limit switch.'
    print 'home', home
    print 'end', end

serCon.close()
serEnc.close()