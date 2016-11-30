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

#########################################################
#      Program to cycle the Chase fridge                #
#########################################################




RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#ADR
#RX202_lookup = np.loadtxt('RX-102A Mean Curve.tbl')# 300mK and 1K stages
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False)
#test = np.float(RX202_interp(4000))
#RX202_temps = RX202_interp(-linear_bridge*1000)

lines = ['-','--','-.']
labels = ['4K P.T.               ','50K HTS            ','50K P.T.             ','50K plate          ','ADR rad shield','4He pump         ','3He pump         ','4He switch        ','3He switch        ','ADR switch        ','4K-1K switch      ','4K plate             ','3He head           ','4He head           ','4K HTS               ','ADR                    ','Head ADR switch']
colors = ['b','g','r','c','m','y','k']

plots = (0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16)

sleep_interval = 60. #seconds
Alarm = 0 # 0 for off 1 for on
Alarm_test = np.zeros(15) #
Alarm_base = np.ones(15)*100.# this is where you fill in your max temp values for the alarm
now = datetime.datetime.now()
date_str = str(now)[0:10]
file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
file_suffix = ''

plt.figure(1,figsize = (19,8))
x = np.arange(-420,0)*1.
print(x[0],x[419])
y = np.ones((420,17))*-1
plt.title("Thermometry")
plt.xlabel("time (mins)")
plt.ylabel("Temperature (K)")
plt.ion()
plt.show()


#create a resourcemanager and see what instruments the computer can talk to
rm = visa.ResourceManager()
rm.list_resources()

#form connections to the two lakeshore temperature sensors available
lk218 = rm.open_resource('GPIB0::2::INSTR')
lk224 = rm.open_resource('GPIB0::12::INSTR')
lr750 = rm.open_resource('GPIB0::4::INSTR')
ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack

#turn on the power supplys 
ag49.write('OUTPut ON')
ag47b.write('OUTPut ON')
ag47t.write('OUTPut ON')


start = time.time() #define a start time
if os.path.isfile(file_prefix + '_temps.txt') == True:
	file_suffix = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
f = open(file_prefix + file_suffix +'_fridge_cycle_temps.txt' ,'w') #open a file to write the temperatures to
i = 0
k = 0
finished = 0 #run until it looks like the fridge cycle has completed
try: #allows you to kill the loop with ctrl c
	while finished == 0: #count the seconds since the start time, and sleep for 1 second between each count
		now2 = time.time()
		now = datetime.datetime.now()
		if str(now)[0:10] != date_str: #if it is a new day start a new file
			f.close()
			date_str = str(now)[0:10]
			file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
			file_suffix = ''
			f = open(file_prefix + file_suffix +'_fridge_cycle_temps.txt' ,'w') #open a file to write the temperatures to
			
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
			try:
				lr750_a_num = np.float(lr750_a[0:8])
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
				if (Alarm_test>Alarm_base).any() == True:
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
			print("test")
			print('#Human readable time. Time (s) since start. Lakeshore temperature sensor 218 T1,3,5,6,8 and 224 C2,C3,C4,C5,D2,D3,D5,A,B',file=f)
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+str(lk218_T1)+' '+str(lk218_T3)+' '+str(lk218_T5)+' '+str(lk218_T6)+' '+str(lk218_T8)+' '+str(lk224_TC2)+' '+str(lk224_TC3)+' '+str(lk224_TC4)+' '+str(lk224_TC5)+' '+str(lk224_TD2)+' '+str(lk224_TD3)+' '+str(lk224_TD5)+' '+str(lk224_A)+' '+str(lk224_B)+' '+str(lk218_T2)+' '+str(lr750_a_temp)+' '+str(lk224_TD1),file = f) #print the temperature and some nonsense numbers to the file
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+str(lk218_T1)+' '+str(lk218_T3)+' '+str(lk218_T5)+' '+str(lk218_T6)+' '+str(lk218_T8)+' '+str(lk224_TC2)+' '+str(lk224_TC3)+' '+str(lk224_TC4)+' '+str(lk224_TC5)+' '+str(lk224_TD2)+' '+str(lk224_TD3)+' '+str(lk224_TD5)+' '+str(lk224_A)+' '+str(lk224_B)+' '+str(lk218_T2)+' '+str(lr750_a_temp)+' '+str(lk224_TD1))
		#time.sleep(60)#sleep for 60 second
		i = i + 1
		
		#fridge cycle crap starts here
		#the way I am doing it is a bit weird we are just continously looping
		#and excuting certain fridge steps if the time is appropriate
		#rather than just do things step by step. 
		#step 1 is open (heat) the ADR switch
		
		# ADR heat switch want to leave open so that the 1K head can cool the ADR
		# but turn off before cycle ADR
		# doesn't cool well if the 4K-1K switch is not on and the film burner is hot
		if t>70*60 and t<110*60: #70,800
			if lk224_TD2<26.:
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 3.5')#3.5
			if lk224_TD2>30.: #temp should drop slowly
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 2.5')#2.5
			if lk224_TD2>35.: #just in case
				ag49.write('INST:SEL OUT1')
				ag49.write('Volt 0')
		else:
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 0')
				
		#Heat up the 4He pump
		if t>0*60 and t<50*60:
			if lk224_TC2<45.:
				ag47t.write('INST:SEL OUT1')
				ag47t.write('Volt 25')
			if lk224_TC2>45.:
				ag47t.write('INST:SEL OUT1')
				ag47t.write('Volt 15') #should creep up
			if lk224_TC2>50.:
				ag47t.write('INST:SEL OUT1')
				ag47t.write('Volt 0')	
		else:
			ag47t.write('INST:SEL OUT1')
			ag47t.write('Volt 0')
			
		#Heat up the He3 pump turn off 50mins after He4 pump is turned off
		if t>30*60 and t<100*60:
			if lk224_TC3<45.:
				ag47t.write('INST:SEL OUT2')
				ag47t.write('Volt 15')
			if lk224_TC3>45.:
				ag47t.write('INST:SEL OUT2')
				ag47t.write('Volt 5')#should increase slowly
			if lk224_TC3>50.:
				ag47t.write('INST:SEL OUT2')
				ag47t.write('Volt 0')
		else:
			ag47t.write('INST:SEL OUT2')
			ag47t.write('Volt 0')
			
		#close (heat) the He4 switch turn on when He4 pump is turned off leave on forever
		if t>50*60 and t<300*60:
			if lk224_TC4<29.:
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 4')
			if lk224_TC4>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 2')
			if lk224_TC4>35.: #just in case
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 0')
		elif t>300*60 and lk224_A<0.5: #keep the switches on until the 300mK stage heats up
			if lk224_TC4<29.:
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 4')
			if lk224_TC4>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 2')
			if lk224_TC4>35.: #just in case
				ag47b.write('INST:SEL OUT1')
				ag47b.write('Volt 0')
		else:
			ag47b.write('INST:SEL OUT1')
			ag47b.write('Volt 0')
			
		#close (heat) the He3 switch turn on when He3 pump is turned off leave on forever
		if t>100*60 and t<300*60:
			if lk224_TC5<30.:
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 3.6')
			if lk224_TC5>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 2')
			if lk224_TC5>35.: #just in case
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 0')
		elif t>300*60 and lk224_A<0.5: #keep the switchs on until 300mK stage warms up
			if lk224_TC5<30.:
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 3.6')
			if lk224_TC5>30.: #temp should drop slowly
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 2')
			if lk224_TC5>35.: #just in case
				ag47b.write('INST:SEL OUT2')
				ag47b.write('Volt 0')	
		else:
			ag47b.write('INST:SEL OUT2')
			ag47b.write('Volt 0')
			
		#monitor when the 300mK stage heats up.
		if t>300*60:
			if lk224_A>0.5:
				print("fridge cycle complete")
				k = k+1
				
		if k>60.: #keep logging for another hour
			finished = 1
		
	f.close() #close the file
	execfile("Temp_monitor.py") #rusume the normal temperature monitoring process
		
except KeyboardInterrupt:
    pass

f.close() #close the file

print("Human interupted the fridge cycle")