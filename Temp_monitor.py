from __future__ import print_function
import numpy as np
import visa
import matplotlib
matplotlib.use('qt4agg')
import matplotlib.pyplot as plt
import time
import datetime
import os
import smtplib
from scipy import interpolate

# to Add a new thermoeter change the call for y line ~41 and the labels and the plots and the print funcitons at the very end

RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#202 ADR sensor
#RX202_lookup = np.loadtxt('RX-102A Mean Curve.tbl') #102 300mK/ 1K sensors
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False)
#test = np.float(RX202_interp(4000))
#RX202_temps = RX202_interp(-linear_bridge*1000)

lines = ['-','--','-.']
labels = ['4K P.T.               ','50K HTS            ','50K P.T.             ','50K plate          ','ADR rad shield','4He pump         ','3He pump         ','4He switch        ','3He switch        ','ADR switch        ','4K-1K switch      ','4K plate             ','3He head           ','4He head           ','4K HTS               ','ADR                    ','Head ADR switch']
colors = ['b','g','r','c','m','y','k']

plots = (0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16)


sleep_interval = 60. #seconds
Alarm = 0 # 0 for off 1 for on
Alarm_base = np.zeros((10,15))
Alarm_test = np.zeros(15)
Alarm_threshold = 2.
now = datetime.datetime.now()
date_str = str(now)[0:10]
file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
file_suffix = ''

plt.figure(1,figsize = (19,10))
ax = plt.gca()
x = np.arange(-420,0)*1.
print(x[0],x[419])
y = np.ones((420,17))*-1
plt.title("Thermometry")
plt.xlabel("time (mins)")
plt.ylabel("Temperature (K)")
plt.ion()
plt.show()




#create a resourcemanager and see what instruments the computer can talk to
#path = os.path.normpath("C:/Program Files/IVI Foundation/VISA/Win64/Lib_x64/msc/visa64.lib")
rm = visa.ResourceManager()
print, rm.list_resources()

#form connections to the two lakeshore temperature sensors available
lk224 = rm.open_resource('GPIB0::12::INSTR')
lk218 = rm.open_resource('GPIB0::2::INSTR')
lr750 = rm.open_resource('GPIB0::4::INSTR')

#double check that you've connected to the lakeshore temperature sensors by asking them their names
print(lk218.query('*IDN?'))
print(lk224.query('*IDN?'))

start = time.time() #define a start time
if os.path.isfile(file_prefix + '_temps.txt') == True:
	file_suffix = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a file to write the temperatures to
i = 0
try: #allows you to kill the loop with ctrl c
	while True: #count the seconds since the start time, and sleep for 1 second between each count
		now2 = time.time()
		now = datetime.datetime.now()
		if str(now)[0:10] != date_str: #if it is a new day start a new file
			f.close()
			date_str = str(now)[0:10]
			file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
			file_suffix = ''
			f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a file to write the temperatures to
			
		t = time.time()-start
		x = np.roll(x,-1)
		x[419] = t/60.
		y = np.roll(y,-1,axis = 0)
		plt.xlim(x[0],x[419])
		plt.ylim(0.1,300)
			
		y[419,0] = lk218_T1 = float(lk218.query('KRDG?1'))
		#print(y[419,0],lk218_T1)
		y[419,14] = lk218_T2 = float(lk218.query('KRDG?2'))
		y[419,1] = lk218_T3 = float(lk218.query('KRDG?3'))
		y[419,2] = lk218_T5 = float(lk218.query('KRDG?5'))
		y[419,3] = lk218_T6 = float(lk218.query('KRDG?6'))
		y[419,4] = lk218_T8 = float(lk218.query('KRDG?8'))
		
		y[419,5] = lk224_TC2 = float(lk224.query('KRDG? C2'))
		y[419,6] = lk224_TC3 = float(lk224.query('KRDG? C3'))
		y[419,7] = lk224_TC4 = float(lk224.query('KRDG? C4'))
		y[419,8] = lk224_TC5 = float(lk224.query('KRDG? C5'))
		y[419,9] = lk224_TD2 = float(lk224.query('KRDG? D2'))
		y[419,10] = lk224_TD3 = float(lk224.query('KRDG? D3'))
		y[419,11] = lk224_TD5 = float(lk224.query('KRDG? D5'))
		
		y[419,12] = lk224_A = float(lk224.query('KRDG? A'))
		y[419,13] = lk224_B = float(lk224.query('KRDG? B'))
		y[419,16] = lk224_TD1 = float(lk224.query('KRDG? D1'))
		lr750_a = lr750.query('GET 0')
		#print(lr750_a)
		if i == 0: # there is some weirdness where the first call returns an empty string
			lr750_a_temp = -1
		if i != 0:
			try: #every once in a while this fails
				lr750_a_num = np.float(lr750_a[0:8])
				print(lr750_a_num)
				y[419,15] = lr750_a_temp = RX202_interp(-lr750_a_num*1000)
			except:
				y[419,15] = lr750_a_temp = -1.
		
		k = 0
		for j in plots:
			#print(y[419,j])
			plt.semilogy(x,y[:,j],color = colors[np.mod(j,7)],linestyle = lines[j/7],linewidth = 2, label = labels[j]+" " +str(y[419,j])[0:5]+"K")
			if i != 0:
				legend.get_texts()[k].set_text(labels[j]+" " +str(y[419,j])[0:5]+"K")
			k = k+1
		if i == 0:					
			legend = plt.legend(ncol = 1,loc =2)
		plt.draw()
		plt.pause(sleep_interval)
		
		if Alarm != 0:
			if i < 10: # get a base reading for the allarm
				Alarm_base[i,0] = lk218_T1
				Alarm_base[i,1] = lk218_T3
				Alarm_base[i,2] = lk218_T5
				Alarm_base[i,3] = lk218_T6
				Alarm_base[i,4] = lk218_T8
				Alarm_base[i,5] = lk224_TC2
				Alarm_base[i,6] = lk224_TC3
				Alarm_base[i,7] = lk224_TC4
				Alarm_base[i,8] = lk224_TC5
				Alarm_base[i,9] = lk224_TD2
				Alarm_base[i,10] = lk224_TD3
				Alarm_base[i,11] = lk224_TD5
				Alarm_base[i,12] = lk224_A
				Alarm_base[i,13] = lk224_B
				Alarm_base[i,14] = lk218_T2
			if i > 10: #trigger the alarm if the temps execeed the threshold
				Alarm_test[0] = lk218_T1
				Alarm_test[1] = lk218_T3
				Alarm_test[2] = lk218_T5
				Alarm_test[3] = lk218_T6
				Alarm_test[4] = lk218_T8
				Alarm_test[5] = lk224_TC2
				Alarm_test[6] = lk224_TC3
				Alarm_test[7] = lk224_TC4
				Alarm_test[8] = lk224_TC5
				Alarm_test[9] = lk224_TD2
				Alarm_test[10] = lk224_TD3
				Alarm_test[11] = lk224_TD5
				Alarm_test[12] = lk224_A
				Alarm_test[13] = lk224_B
				Alarm_test[14] = lk218_T2
				if (Alarm_test>np.mean(Alarm_base,axis = 0)+Alarm_threshold).any() == True:
					print("Alarm Alarm")
					if Alarm == 1:
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
						server.sendmail(fromaddr, toaddrs, msg)
						toaddrs  = '3038192582@tmomail.net'
						server.sendmail(fromaddr, toaddrs, msg)
						server.quit()	
					Alarm = 2
				
		if i == 0:
			print('#Human readable time. Time (s) since start. Lakeshore temperature sensor 218 T1,3,5,6,8 and 224 C2,C3,C4,C5,D2,D3,D5,A,B',file=f)
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+str(lk218_T1)+' '+str(lk218_T3)+' '+str(lk218_T5)+' '+str(lk218_T6)+' '+str(lk218_T8)+' '+str(lk224_TC2)+' '+str(lk224_TC3)+' '+str(lk224_TC4)+' '+str(lk224_TC5)+' '+str(lk224_TD2)+' '+str(lk224_TD3)+' '+str(lk224_TD5)+' '+str(lk224_A)+' '+str(lk224_B)+' '+str(lk218_T2)+' '+str(lr750_a_temp)+' '+str(lk224_TD1),file = f) #print the temperature and some nonsense numbers to the file
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+str(lk218_T1)+' '+str(lk218_T3)+' '+str(lk218_T5)+' '+str(lk218_T6)+' '+str(lk218_T8)+' '+str(lk224_TC2)+' '+str(lk224_TC3)+' '+str(lk224_TC4)+' '+str(lk224_TC5)+' '+str(lk224_TD2)+' '+str(lk224_TD3)+' '+str(lk224_TD5)+' '+str(lk224_A)+' '+str(lk224_B)+' '+str(lk218_T2)+' '+str(lr750_a_temp)+' '+str(lk224_TD1))
		#time.sleep(sleep_interval)#sleep for 60 second
		i = i + 1
		
							
		
		
		
except KeyboardInterrupt:
    pass

f.close() #close the file

print("Temperature monitoring disabled")