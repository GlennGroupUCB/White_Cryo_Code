import numpy as np
import visa

#A file containing all functions which plot data

def PlotPwr();
	# plot the power levels	
	plt.subplot(gs[2,:])
	k = 0
	for j in range(0,len(volt)):
		plt.plot(x,volt_y[:,j],color = colors[np.mod(j,7)],linestyle = lines[j/7],linewidth = 2, label = power_labels[j]+ " " +str(volt_y[419,j])[0:4]+"V " + str(curr_y[419,j])[0:6]+"A")
		if i != 0:
			legend_power.get_texts()[k].set_text(power_labels[j]+" " +str(volt_y[419,j])[0:4]+"V "+ str(curr_y[419,j])[0:6]+"A")
		k = k+1
	if i ==0:
		legend_power= plt.legend(ncol = 1,loc = 2)		
	plt.xlim(x[0],x[419])
	plt.ylim(0,30)

	plt.draw()


	if Alarm != 0:
		Alarm_test = y[419,:]*Alarm_on #0 if not on otherwise actual temperature
		if (Alarm_test>(Alarm_value +.001)).any() == True:
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
				toaddrs  = '5308487272@pm.sprint.com'
				server.sendmail(fromaddr, toaddrs, msg)
				server.quit()	
			Alarm = 2
