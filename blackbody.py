from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit




#########################################################
#      Program to plot BlackBody   from file            #
#########################################################

#CHANGELOG
b = []
t = []

#get temp and time
with open('2017-05-16_10_44_temps.txt','r') as f:
	data = f.readlines()[1:] #skips first line
	for line in data:
		#print(line)
             str = line
             x = str.split()
    
             #if 469 < float(x[2]) < 9300:
             #if 9300 < float(x[2]) < 17000:
             #if 17500 < float(x[2]) < 24000:
             if 24500 < float(x[2]) < 100000:
                 #print(x[2])
                 b.append(x[6])
                 t.append(x[2])
	
	
#print(t) 
#get voltages and current
'''with open('2017-05-16_10_25_VI.txt','r') as v:
	data = v.readlines()[1:] #skips first line
	
	for line in data:
		#print(line)
		str = line
		y = str.split()
		#print(y[6])
		volt.append(y[4])
'''

b = np.array(b, dtype = float)
t = np.array(t, dtype = float) - float(t[0])

guess = (10, 1e-6, -38)


def expo_fnc(t, A, k, c):
    return A-c*np.exp(-k*t)
 

popt, pcov = curve_fit(expo_fnc, t, b, guess)

y = expo_fnc(t, *popt)

tau = 1/popt[1]
print(tau)



'''y = np.polyfit(t, b, 5)
f = np.poly1d(y)
print(f)
'''
plt.figure(1)
plt.plot(t,y, linewidth = 2.0)

#plt.plot(t,f(t), linewidth = 2.0)

plt.plot(t, b, 'ro')
plt.xlabel('t (sec)')
plt.ylabel('K')
plt.title('Black Body Temp. vs. Time')
plt.show() 