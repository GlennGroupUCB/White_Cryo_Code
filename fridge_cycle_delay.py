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
import matplotlib.gridspec as gridspec
from functions import read_power_supplies, get_temps, initialize
from scipy import interpolate

#########################################################
#      Program to cycle the Chase fridge                #
#########################################################



#CHANGE LOG


#create a resourcemanager and see what instruments the computer can talk to
rm = visa.ResourceManager()
rm.list_resources()

ag49 = rm.open_resource('GPIB0::3::INSTR') #power supply 3649 in the upper RH of Rack
ag47b = rm.open_resource('GPIB0::5::INSTR') #power supply 3647 on bottom row of power supplies
ag47t = rm.open_resource('GPIB0::15::INSTR') #power supply 3647 on top row of rack

#turn on the power supplys
ag49.write('OUTPut ON')
ag47b.write('OUTPut ON')
ag47t.write('OUTPut ON')


RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')#202 ADR sensor look up table
RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False) # interpolates the temperature when in between lookup table values

#initialize plot resources from functions
lines, colors, labels, plots = initialize()

# turn on alarm on for certain values
#                     4K P.T--4K HTS--50K HTS--Black Body--50K P.T.--50K Plate--ADR Shield--4He Pump--3He Pump--4He Switch--3 He Switch--300 mK Shield--ADK Switch--4-1K Switch--1K Shield--3He Head--4He Head--ADR--
Alarm_on = np.array((  0,     0,       0,         0,           0,             0,       0,        0,           0,          0,         0,             0,        0,      0,       0,    0,      0, 	0))
Alarm_value =np.array((0,     0,       0,         0,           0,             0,       0,        0,           0,          0,         0,             0,        0,      0,       0,    0,      0, 	0))

sleep_interval = 10. #seconds change back
Alarm = 0 # 0 for off 1 for on

now = datetime.datetime.now()
date_str = str(now)[0:10]
# we want the file prefix to reflect the date in which the temperature data is taken
file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
file_suffix = ''
file_prefix2 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Voltage_Current/" + date_str
file_suffix2 = ''

plt.figure(1,figsize = (21,11))
ax = plt.gca() #need for changing legend labels
x = np.arange(-420,0)*1. # initalize the x axis i.e. time going 420 mins into the past
print(x[0],x[419])
y = np.ones((420,19))*-1 #initalize array to hold temperautere
volt_y = np.zeros((420,6)) #initialize array to hold voltages
curr_y = np.zeros((420,6)) #initialize array to hold currents


plt.title("Thermometry")
plt.xlabel("time (mins)")
plt.ylabel("Temperature (K)")
plt.ion() 					#need for constantly updating plot
gs = gridspec.GridSpec(3,3)	#allows for custom subplot layout
plt.show()

start = time.time() #define a start time
if os.path.isfile(file_prefix + '_temps_fridgecycle.txt') == True: #check if there is already a file with the prefix we are trying to use
	#If a file already exists add a suffix to the end that consist of the time it was created so it can be distinguished from the original file
	file_suffix = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
f = open(file_prefix + file_suffix +'_temps_fridgecycle.txt' ,'w') #open a file to write the temperatures to

if os.path.isfile(file_prefix2 + '_VI_fridgecycle.txt') == True:
	file_suffix2 = '_'+str(datetime.datetime.now())[11:13]+'_'+str(datetime.datetime.now())[14:16]
g = open(file_prefix2 + file_suffix2 +'_VI_fridgecycle.txt' ,'w')


i = 0 #initialize a counter
k = 0
try: #allows you to kill the loop with ctrl c
	while True: #Just loop for every never stopping the monitoring of the temperatures
		now = datetime.datetime.now()
		if str(now)[0:10] != date_str: #checks if the day has changed (i.e.) at midnight,if it is a new day start a new file
			f.close() #close the old file
			date_str = str(now)[0:10]
			file_prefix =  "C:/Users/tycho/Desktop/White_Cryo_Code/Temps/" + date_str
			file_suffix = ''
			file_prefix2 =  "C:/Users/tycho/Desktop/White_Cryo_Code/Voltage_Current/" + date_str


			f = open(file_prefix + file_suffix +'_temps.txt' ,'w') #open a new file to write the temperatures to
			g = open(file_prefix2 + file_suffix +'_VI.txt' ,'w')



		t = time.time()-start #current time
		x = np.roll(x,-1) #shift the time array by 1 interval
		x[419] = t/60. #record current time to last position of time array
		y = np.roll(y,-1,axis = 0) # shift temperature array by 1 interval
		volt_y = np.roll(volt_y,-1,axis = 0) #shift voltage array by 1 interval
		curr_y = np.roll(curr_y,-1,axis = 0) #shift current array by 1 interval

		#grab temperatures and store them to the temperature array
		temps = get_temps()
		y[419,:] = temps

		lk218_T1 = y[419,0]
		lk218_T2 = y[419,1]
		lk218_T3 = y[419,2]
		lk218_T4 = y[419,3]
		lk218_T5 = y[419,4]
		lk218_T6 = y[419,5]
		lk218_T8 = y[419,6]
		lk224_TC2 = y[419,7]
		lk224_TC3 = y[419,8]
		lk224_TC4 = y[419,9]
		lk224_TC5 = y[419,10]
		lk224_TD1 = y[419,11]
		lk224_TD2 = y[419,12]
		lk224_TD3 = y[419,13]
		lk224_TD4 = y[419,14]
		lk224_TD5 = y[419,15]
		lk224_A = y[419,16]
		lk224_B = y[419,17]
		lr750_a_temp = y[419,18]



		#fridge cycle crap starts here
		#the way I am doing it is a bit weird we are just continously looping
		#and excuting certain fridge steps if the time is appropriate
		#rather than just do things step by step.
		#step 1 is open (heat) the ADR switch

		# ADR heat switch want to leave open so that the 1K head can cool the ADR
		# but turn off before cycle ADR
		# doesn't cool well if the 4K-1K switch is not on and the film burner is hot
		if t>120*60 and t<180*60: #70,800
			ag49.write('INST:SEL OUT1')
			ag49.write('Volt 1.5')#3.5 #Afyhrie changed from 1.75 to 1.5 on June 28 2017
			#to make sure the ADR switch doesn't heat above 17 K
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

		seconds = int(t)
		minutes = int(t/60)
		if seconds >= 60:
			seconds = int(t-(60*minutes))
		print('Cycle duration: ',minutes, ':', seconds)

		k = 0 #intiialize a counter

		plt.subplot(gs[0:2,:]) #create top subplot
		for j in plots: #plot all of the temperatures with appropriate labels
			plt.semilogy(x,y[:,j],color = colors[np.mod(j,7)],linestyle = lines[j/7],linewidth = 2, label = labels[k]+" " +str(y[419,j])[0:5]+"K")
			if i != 0:
				legend.get_texts()[k].set_text(labels[k]+" " +str(y[419,j])[0:5]+"K") #if it is not the first time ploting rewrite the legend with the new temps
			k = k+1
		#if it is the first time ploting generate the legend
		if i == 0:
			legend = plt.legend(ncol = 2,loc = 1, bbox_to_anchor=(0.2, 1.15), fancybox=True, shadow=True)
		plt.xlim(x[0],x[419])
		plt.ylim(0.1,300)

		#grab voltages and current from power supplies
		power_labels, volt, curr = read_power_supplies()
		volt_y[419,:]= volt
		curr_y[419,:]= curr


		# plot the power levels
		plt.subplot(gs[2,:])
		k = 0
		for j in range(0,len(volt)):
			plt.plot(x,volt_y[:,j],color = colors[np.mod(j,7)],linestyle = lines[j/7],linewidth = 2, label = power_labels[j]+ " " +str(volt_y[419,j])[0:4]+"V " + str(curr_y[419,j])[0:6]+"A")
			if i != 0:
				legend_power.get_texts()[k].set_text(power_labels[j]+" " +str(volt_y[419,j])[0:4]+"V "+ str(curr_y[419,j])[0:6]+"A")#if it is not the first time ploting rewrite the legend with the new temps
			k = k+1
		if i ==0:
			legend_power= plt.legend(ncol = 2,loc = 2, fancybox=True, shadow=True)	 #If it is the first time plotting generate the legend
		plt.xlim(x[0],x[419])
		plt.ylim(0,30)




		#Alarm function
		if Alarm != 0: #if the alarm is turned on proceed
			Alarm_test = y[419,:]*Alarm_on #0 if not on otherwise actual temperature
			if (Alarm_test>(Alarm_value +.001)).any() == True: #have any of the alarm values been reached
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


		if i == 0: #if it is the first time writing to file put in a header
			# not sure this header is up to date also need to add header if a new day has started
			print('#Human readable time. Time (s) since start. Lakeshore temperature sensor 218 T1,2,3,4,5,6,8 and 224 C2,C3,C4,C5,D1,D2,D3,D4,D5,A,B, LR750',file=f)
			print('#Human readable time. Time (s) since start. V @ ag47t. A @ ag47t. V @ ag47b. A @ ag47b. V @ ag49. A @ ag49.', file=g)

		# write temps to file
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(y[419,0])+' '+ str(y[419,1])+' '+ str(y[419,2])+' '+ str(y[419,3])+' '+ str(y[419,4])+' '+ str(y[419,5])+' '+ str(y[419,6])+' '+ str(y[419,7])+' '+ str(y[419,8])+' '+ str(y[419,9])+' '+ str(y[419,10])+' '+ str(y[419,11])+' '+ str(y[419,12])+' '+ str(y[419,13])+' '+ str(y[419,14])+' '+ str(y[419,15])+' '+ str(y[419,16])+' '+ str(y[419,17])+' '+str(y[419,18]), file = f) #print the temperature and some nonsense numbers to the file
		for k in range(0,len(temps)):
			# write to command prompt
			print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(y[419, k]))



		#print the current and voltage to the file
		volt_str = ''
		for k in range(0, len(volt)):
			volt_str = volt_str + str(volt_y[419,k])
			if k!=len(volt)-1:
				volt_str = volt_str + ","
			#print(str(volt_y[419, k])+'V '+str(curr_y[419, k])+'I ', file = g)

			# write to command prompt
			print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ str(volt_y[419, k])+' '+ str(curr_y[419, k]))
		print(str(now)+' '+ str(np.round(t,3)).strip()+' '+ volt_str,file = g)


		i = i + 1 #icrement the counter

		plt.pause(sleep_interval) # pause for sleep interval before looping again


except KeyboardInterrupt:
    pass



print("Human interupted the fridge cycle")
