from __future__ import print_function
import numpy as np
import visa
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib

#We should proabably just turn on one pump at a time to not overload the 4K stage and heat up all the switches

rm = visa.ResourceManager()
rm.list_resources()
ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag49.write('OUTPut ON')
ag47t.write('OUTPut ON')
ag47b.write('OUTPut ON')

ag47t.write('INST:SEL OUT1')#Helium 4 pump
ag47t.write('Volt 0')

ag47t.write('INST:SEL OUT2')#Helium 3 pump
ag47t.write('Volt 0')

ag49.write('INST:SEL OUT1')#ADR
ag49.write('Volt 0')
ag49.write('INST:SEL OUT2')#1K-4K
ag49.write('Volt 0')
ag47b.write('INST:SEL OUT1')# helium 4 heat switch
ag47b.write('Volt 0')
ag47b.write('INST:SEL OUT2')# helium 3 heat switch
ag47b.write('Volt 0')


