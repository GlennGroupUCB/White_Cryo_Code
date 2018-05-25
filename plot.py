import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from scipy import interpolate
import matplotlib.gridspec as gridspec
import StringIO



# program to let you plot historical cryostat data
# written by Tim Childers
# date: 24/5/2017

#TO DO:
# add ADR to plotting
#include pressure


#Plotting resources
labels = ['4K P.T.','4K HTS','50K HTS','Black Body','50K P.T.','50K Plate','ADR Shield','4He Pump','3He Pump','4He Switch','3He Switch','300 mK Shield','ADR Switch','4-1K Switch','1K Shield','4K Plate','3He Head','4He Head','ADR']
power_labels = ("He4 pump", "He3 pump", "He4 switch", "He3 switch", "ADR switch", "4K 1K switch")
plots = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18)
visible = (True,)*19
# These are the "Tableau 20" colors as RGB.
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
			 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
			 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
			 (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
			 (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(tableau20)):
	r, g, b = tableau20[i]
	tableau20[i] = (r / 255., g / 255., b / 255.)

def main():

	#command line interface
	print('Provide a file name string or list of filenames seperated by commas')
	print('i.e. ./Temps/2016-10-20_temps.txt or ./Temps/2016-10-19_temps.txt,./Temps/2016-10-19_temps.txt')
	filelist = raw_input('Enter filename(s):')
	linear = raw_input('Would you like a linear y axis? (y/n):')
	power = raw_input('Would you like to plot power? (y/n):')
	#create subplot for power if selected
	if power == "y":
		figure, (ax,ax2) = plt.subplots(2, sharex=True)
		filelist2 = raw_input('Enter filename(s):')

	else:
		#single plot format
		figure, ax = plt.subplots()
}
	#filelist = "./Temps/2017-05-24_temps.txt,./Temps/2017-05-25_temps.txt"
	#filelist = "./Temps/2017-07-06_temps.txt"
	#filelist2= "./Voltage_Current/2017-05-24_VI.txt,./Voltage_Current/2017-05-25_VI.txt"
	#filelist2= "./Voltage_Current/2017-05-24_VI.txt"

	#arrays for time,temperature
	x = []
	y = []

	#if filelist isnt empty:
	if filelist != ' ':
		#if only one file is given:
		if filelist.find(',')==-1:
			#load file, skip first row(header), read columns 2-21
			data = np.loadtxt(filelist, delimiter = ' ',skiprows = 1,usecols = range(2,21))
			start = 0				#first row
			stop =  data.shape[0]-2	#dimension of array, -2 b/c skip 1st row and empty line


			for i in range(1,len(plots)):
				x.append(data[start:stop,0]/60.-data[start,0]/60)
				y.append(data[start:stop,i])
				plt.xlim(0,data[stop,0]/60.-data[start,0]/60)

			#make log plot
			if linear == 'n':
				ax.set_yscale('log')
				ax.set_ylim(.1,1000)

			if linear != 'y' or 'n':
				print('Please select y or n')
				exit

			#create all subplots
			p0, = ax.plot(x[0],y[0], lw=2, c = tableau20[0])
			p1, = ax.plot(x[1],y[1], lw=2, c = tableau20[1])
			p2, = ax.plot(x[2],y[2], lw=2, c = tableau20[2])
			p3, = ax.plot(x[3],y[3], lw=2, c = tableau20[3])
			p4, = ax.plot(x[4],y[4], lw=2, c = tableau20[4])
			p5, = ax.plot(x[5],y[5], lw=2, c = tableau20[5])
			p6, = ax.plot(x[6],y[6], lw=2, c = tableau20[6])
			p7, = ax.plot(x[7],y[7], lw=2, c = tableau20[7])
			p8, = ax.plot(x[8],y[8], lw=2, c = tableau20[8])
			p9, = ax.plot(x[9],y[9], lw=2, c = tableau20[9])
			p10, = ax.plot(x[10],y[10], lw=2, c = tableau20[10])
			p11, = ax.plot(x[11],y[11], lw=2, c = tableau20[11])
			p12, = ax.plot(x[12],y[12], lw=2, c = tableau20[12])
			p13, = ax.plot(x[13],y[13], lw=2, c = tableau20[13])
			p14, = ax.plot(x[14],y[14], lw=2, c = tableau20[14])
			p15, = ax.plot(x[15],y[15], lw=2, c = tableau20[15])
			p16, = ax.plot(x[16],y[16], lw=2, c = tableau20[16])
			p17, = ax.plot(x[17],y[17], lw=2, c = tableau20[17])
			#comment 18 out if you don't have ADR data
			#p18, = ax.plot(x[18],y[18], lw=2, c = tableau20[0])

		#more than one file given
		else:
			filenames = [k.strip() for k in filelist.split(',')]
			data = np.loadtxt(filenames[0], delimiter = ' ',skiprows = 1,usecols = range(2,21))

			for j in range(1,len(filenames)):
				data2 = np.loadtxt(filenames[j], delimiter = ' ',skiprows = 1,usecols = range(2,21))
				data2[:,0] = data2[:,0] +data[data.shape[0]-2,0] -data2[0,0]
				data = np.vstack((data,data2))

			start = 0
			stop =  data.shape[0]-2

			for i in range(1, len(plots)):
				x.append(data[start:stop,0]/60.-data[start,0]/60.)
				y.append(data[start:stop,i])

			if linear == 'n':
				ax.set_yscale('log')
				ax.set_ylim(.1,1000)

			p0, = ax.plot(x[0],y[0], lw=2, c = tableau20[0])
			p1, = ax.plot(x[1],y[1], lw=2, c = tableau20[1])
			p2, = ax.plot(x[2],y[2], lw=2, c = tableau20[2])
			p3, = ax.plot(x[3],y[3], lw=2, c = tableau20[3])
			p4, = ax.plot(x[4],y[4], lw=2, c = tableau20[4])
			p5, = ax.plot(x[5],y[5], lw=2, c = tableau20[5])
			p6, = ax.plot(x[6],y[6], lw=2, c = tableau20[6])
			p7, = ax.plot(x[7],y[7], lw=2, c = tableau20[7])
			p8, = ax.plot(x[8],y[8], lw=2, c = tableau20[8])
			p9, = ax.plot(x[9],y[9], lw=2, c = tableau20[9])
			p10, = ax.plot(x[10],y[10], lw=2, c = tableau20[10])
			p11, = ax.plot(x[11],y[11], lw=2, c = tableau20[11])
			p12, = ax.plot(x[12],y[12], lw=2, c = tableau20[12])
			p13, = ax.plot(x[13],y[13], lw=2, c = tableau20[13])
			p14, = ax.plot(x[14],y[14], lw=2, c = tableau20[14])
			p15, = ax.plot(x[15],y[15], lw=2, c = tableau20[15])
			p16, = ax.plot(x[16],y[16], lw=2, c = tableau20[16])
			p17, = ax.plot(x[17],y[17], lw=2, c = tableau20[17])



	else:
		print('Please specify a filename')
		exit


	#this provides functionality to checkbuttons
	def func(label):
		if label== labels[0]:
			p0.set_visible(not p0.get_visible())
		elif label== labels[1]:
			p1.set_visible(not p1.get_visible())
		elif label== labels[2]:
			p2.set_visible(not p2.get_visible())
		elif label== labels[3]:
			p3.set_visible(not p3.get_visible())
		elif label== labels[4]:
			p4.set_visible(not p4.get_visible())
		elif label== labels[5]:
			p5.set_visible(not p5.get_visible())
		elif label== labels[6]:
			p6.set_visible(not p6.get_visible())
		elif label== labels[7]:
			p7.set_visible(not p7.get_visible())
		elif label== labels[8]:
			p8.set_visible(not p8.get_visible())
		elif label== labels[9]:
			p9.set_visible(not p9.get_visible())
		elif label== labels[10]:
			p10.set_visible(not p10.get_visible())
		elif label== labels[11]:
			p11.set_visible(not p11.get_visible())
		elif label== labels[12]:
			p12.set_visible(not p12.get_visible())
		elif label== labels[13]:
			p13.set_visible(not p13.get_visible())
		elif label== labels[14]:
			p14.set_visible(not p14.get_visible())
		elif label== labels[15]:
			p15.set_visible(not p15.get_visible())
		elif label== labels[16]:
			p16.set_visible(not p16.get_visible())
		elif label== labels[17]:
			p17.set_visible(not p17.get_visible())
		#elif label== labels[18]:
			#p18.set_visible(not p18.get_visible())
		plt.draw()


	rax = plt.axes([0.8, 0.4, 0.20, 0.55])		#checkbox layout
	check = CheckButtons(rax, labels, visible)	#creates box
	for r in check.rectangles:					#allows editing of checkboxes
		r.set_width(0.1)

	[rec.set_facecolor(tableau20[i]) for i, rec in enumerate(check.rectangles)]	#sets checkbox color
	check.on_clicked(func) #calls check function

	#plot voltages
	if power=='y' and filelist2 != '':
		t=[]
		v1=[]
		v2=[]
		v3=[]
		a1=[]
		a2=[]
		a3=[]
		#one file given
		if filelist2.find(',')==-1:
			with open(filelist2, 'r') as f:
				read = f.readlines()[1:]
				for line in read:
					str = line
					x1 = str.split()
					#print(x1)
					t.append(x1[2])
					x2 = x1[3].split(',')
					#print(x2)
					v1.append(x2[0])
					v2.append(x2[2])
					v3.append(x2[4])
					a1.append(x2[1])
					a2.append(x2[3])
					a3.append(x2[5])
			t = (np.array(t, dtype=float)-float(t[0]))/60.
		#more than one filename
		else:
			filenames2 = [i.strip() for i in filelist2.split(',')]
			s = open(filenames2[0]).read().replace(',',' ')		#replaces commas with spaces for delimeter to work
			data3 = np.loadtxt(StringIO.StringIO(s), delimiter = ' ',skiprows = 1,usecols = range(2,9))
			#print(s)
			for j in range(1,len(filenames)):
				#print(filenames2[j])
				s = open(filenames2[j]).read().replace(',',' ')
				data4 = np.loadtxt(StringIO.StringIO(s), delimiter = ' ',skiprows = 1,usecols = range(2,9))
				data4[:,0] = data4[:,0] +data3[data3.shape[0]-2,0] -data4[0,0]
				data3 = np.vstack((data3,data4))
			start = 0
			stop = data3.shape[0]-2
			t=data3[start:stop,0]/60.-data3[start,0]/60

			v1=data3[start:stop,1]
			v2=data3[start:stop,3]
			v3=data3[start:stop,5]
			a1=data3[start:stop,2]
			a2=data3[start:stop,4]
			a3=data3[start:stop,6]

		ax2.plot(t,v1)
		ax2.plot(t,v2)
		ax2.plot(t,v3)
		ax2.set_xlabel("time (min)")
		ax2.set_ylabel("Voltage (V)")
		ax2.legend(labels=power_labels, loc=4)

	ax.set_title("Thermometry")
	ax.set_ylabel("Temperature (K)")
	plt.show()



if __name__=="__main__":
	main()
