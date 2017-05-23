import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import os
import sys
from functions import initialize
# program to let you plot historical temperature data
# written by Jordan Wheeler
# date: 11/17/2016
# the sytax for using this is python plot_temps.py "filename"
#modified for implementatoion with functions.py




lines, colors, labels, plots = initialize()


if __name__=='__main__':
	if len(sys.argv) < 2:
		print('Provide a file name string or list of filenames seperated by commas')
		print('i.e. ./Temps/2016-10-20_temps.txt or ./Temps/2016-10-19_temps.txt,./Temps/2016-10-19_temps.txt')
		print('also if you would like a linear y axis specify the string linear as the second variable')
		print('if you would like to add power as a plot, specify the string power as the second variable')
		sys.exit()
	else:
		if len(sys.argv)>2:
			if sys.argv[2] == 'linear':
				linear = 1
			if sys.argv[2] == 'power':
				power = 1
			else:
				linear = 0


		filelist = sys.argv[1]
		print filelist

		RX202_lookup = np.loadtxt('RX-202A Mean Curve.tbl')
		RX202_interp = interpolate.interp1d(RX202_lookup[:,1], RX202_lookup[:,0],fill_value = 0.,bounds_error = False)
#test = np.float(RX202_interp(4000))
#RX202_temps = RX202_interp(-linear_bridge*1000)

		if filelist.find(",")==-1:
			data = np.loadtxt(filelist, delimiter = ' ',skiprows = 1,usecols = range(2,20))
			print(data)
			start = 0
			stop =  data.shape[0]-2
			plt.figure(figsize = (17,8))
			for i in plots:
				plt.plot(data[start:stop,0]/60.-data[start,0]/60,data[start:stop,i+1],linestyle = lines[i/7],linewidth = 2, label = labels[i])

			plt.xlim(0,data[stop,0]/60.-data[start,0]/60)
			if linear ==0:
				plt.yscale('log')
				plt.ylim(.1,1000)
				plt.legend(ncol = 5,loc ='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, shadow=True)
			else:
				plt.legend(ncol = 5,loc ='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, shadow=True)
			plt.xlabel("time (mins)")
			plt.ylabel("Temperature (K)")
			#plt.savefig(filelist[0:-4] + ".pdf")

			plt.show()
		else:
			filenames = [x.strip() for x in filelist.split(',')]
			data = np.loadtxt(filenames[0], delimiter = ' ',skiprows = 1,usecols = range(2,20))


			for j in range(1,len(filenames)):

				data2 = np.loadtxt(filenames[j], delimiter = ' ',skiprows = 1,usecols = range(2,20))
				data2[:,0] = data2[:,0] +data[data.shape[0]-2,0] -data2[0,0]
				data = np.vstack((data,data2))



			plt.figure(figsize = (17,8))
			start = 0
			stop =  data.shape[0]-2
			for i in plots:
				plt.plot(data[start:stop,0]/60.-data[start,0]/60,data[start:stop,i+1],linestyle = lines[i/7],linewidth = 2, label = labels[i])

			plt.xlim(0,data[stop,0]/60.-data[start,0]/60)
			if linear == 0:
				plt.yscale('log')
				plt.ylim(.1,1000)
				plt.legend(ncol = 5,loc ='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, shadow=True)
			else:
				plt.legend(ncol = 5,loc ='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, shadow=True)
			plt.xlabel("time (mins)")
			plt.ylabel("Temperature (K)")
			#plt.savefig(filelist[j][0:-4] + ".pdf")

			plt.show()