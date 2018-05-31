import numpy as np
from monitor_plot import MonitorPlot
import time

# Custom implementation of the functions.py file that generates random data. Used to test the MonitorPlot class.
# Also contains the direct testing code for MonitorPlot

def initialize():
	lines = ['-', '--', '-.']
	colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
	labels = [
		'4K P.T.               ',
		'4K HTS             ',
		'50K HTS           ',
		'Black Body       ',
		'50K P.T.            ',
		'50K Plate         ',
		'ADR Shield      ',
		'4He Pump        ',
		'3He Pump        ',
		'4He Switch       ',
		'3He Switch       ',
		'300 mK Shield   ',
		'ADR Switch        ',
		'4-1K Switch       ',
		'1K Shield           ',
		'4K Plate            ',
		'3He Head          ',
		'4He Head          ',
		'ADR                   '
	]
	plots = (0, 1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
	return (lines, colors, labels, plots)


def get_press():
	return np.random.lognormal(0, 2)


def get_temps():
	return np.random.lognormal(1, 1, size=19)


def read_power_supplies():
	labels = ('He4 pump', 'He3 pump', 'He4 switch', 'He3 switch', 'ADR switch', '4K 1K switch')
	return (labels, np.random.normal(15, 5, size=6), np.random.normal(15, 5, size=6))




mplot = MonitorPlot(5, 420)
mplot.show()

start = time.time()
while True:
	# Get the new data
	new_temps = get_temps()
	new_press = get_press()
	_, new_volts, new_amps = read_power_supplies()

	# Update the plot
	mplot.update(time.time() - start, new_temps, new_volts, new_amps, new_press)

	# Wait
	mplot.wait()