import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import gridspec

# This file contains the class for plotting an updatable interactive plot to track instrumentation values. This class
# can be copied and modified to easily support new sets of plots and other data.

# Revision History:
#   5/29/18 - Sean Moss - Initial version

class MonitorPlot:
	"""
	Contains the plot information and data to monitor various information about the refridgeration system.
	
	:ivar float sleep_interval: The amount of time between plot updates
	:ivar int history_size: The number of data points to keep in history
	:ivar ndarray T_data: The temperature data array, size: (hist_size, 19)
	:ivar ndarray V_data: The voltage data array, size: (hist_size, 6)
	:ivar ndarray A_data: The current data array, size: (hist_size, 6)
	:ivar ndarray P_data: The pressure data array, size: (hist_size, 1)
	"""

	_LINES = [ '-', '--', '-.' ]
	_COLORS = [ 'b', 'g', 'r', 'c', 'm', 'y', 'k' ]
	_T_LABELS = [
		'4K P.T.', '4K HTS', '50K HTS', 'Black Body', '50K P.T.', '50K Plate', 'ADR Shield', '4He Pump', '3He Pump',
		'4He Switch', '3He Switch', '300 mK Shield', 'ADR Switch', '4-1K Switch', '1K Shield', '4K Plate', '3He Head',
		'4He Head', 'ADR'
	]
	_V_LABELS = [
		'He4 pump', 'He3 pump', 'He4 switch', 'He3 switch', 'ADR switch', '4K 1K switch'
	]

	@staticmethod
	def _get_line_style(i):
		return MonitorPlot._LINES[i // 7]

	@staticmethod
	def _get_line_color(i):
		return MonitorPlot._COLORS[int(i % 7)]

	@staticmethod
	def get_temp_labels():
		return MonitorPlot._T_LABELS

	@staticmethod
	def get_volt_labels():
		return MonitorPlot._V_LABELS

	@property
	def sleep_interval(self):
		return self._sleep

	@property
	def history_size(self):
		return self._hist_size


	def __init__(self, sleep_interval, hist_size):
		"""
		Creates and opens the new plot with default data, ready for updating in the future.
		
		:param float sleep_interval: The number of seconds to wait between plot updates.
		:param int hist_size: The number of wait intervals to plot and keep in memory as history.
		"""
		# Save the parameters
		self._sleep = float(sleep_interval)
		self._sleep_minutes = sleep_interval / 60
		self._hist_size = int(hist_size)

		# Set up the data history arrays
		self._time_data = np.arange(-hist_size, 0) * self._sleep_minutes
		self.T_data = np.ones((hist_size, 19)) * -1
		self.V_data = np.zeros((hist_size, 6))
		self.A_data = np.zeros((hist_size, 6))
		self.P_data = np.zeros((hist_size, 1))

		# Prepare the figure
		self._fig = plt.figure(figsize=(21, 11))
		pgrid = gridspec.GridSpec(4, 1)
		self._T_plot = self._fig.add_subplot(pgrid[0:2, 0])
		self._V_plot = self._fig.add_subplot(pgrid[(2, 0)], sharex=self._T_plot)
		self._P_plot = self._fig.add_subplot(pgrid[(3, 0)], sharex=self._T_plot)
		self._fig.subplots_adjust(hspace=0)

		# Style the plots
		self._fig.suptitle('Thermometry', fontsize='xx-large')
		self._T_plot.set_ylabel('Temperature (K)')
		self._V_plot.set_ylabel('Voltage (V)')
		self._P_plot.set_ylabel('Pressure (mBar)')
		self._P_plot.set_xlabel('Time (mins)')
		self._T_plot.set_ylim((0.05, 300))
		self._V_plot.set_ylim((0, 30))
		self._P_plot.set_ylim((0.0001, 1300.0))

		# Create and cache the data lines
		self._T_lines = [
			self._T_plot.semilogy(self._time_data, self.T_data[:, i], color=MonitorPlot._get_line_color(i), linestyle=MonitorPlot._get_line_style(i), label=('{:<15}{:>7.3f} K').format(MonitorPlot._T_LABELS[i], self.T_data[:, i][-1]))
			for i in range(19)
		]
		self._V_lines = [
			self._V_plot.plot(self._time_data, self.V_data[:, i], color=MonitorPlot._get_line_color(i), label=('{:<15}{:>7.3f} V {:>7.3f} A').format(MonitorPlot._V_LABELS[i], self.V_data[:, i][-1], self.A_data[:, i][-1]))
			for i in range(6)
		]
		self._P_lines = [
			self._P_plot.semilogy(self._time_data, self.P_data[:, i], label=('Pressure {:>7.3f} mbar').format(self.P_data[:,i][-1]))
			for i in range(1)
		]

		# Create and cache the legends
		self._T_leg = self._T_plot.legend(loc='upper left')
		self._V_leg = self._V_plot.legend(loc='upper left')
		self._P_leg = self._P_plot.legend(loc='upper left')
		plt.setp(self._T_leg.texts, family='consolas')
		plt.setp(self._V_leg.texts, family='consolas')
		plt.setp(self._P_leg.texts, family='consolas')


	def show(self):
		"""
		Opens the plot window, in interactive mode.
		"""
		plt.ion()
		plt.show()


	def update(self, time, Ts, Vs, As, Ps, redraw=True):
		"""
		Update the plot with the data from the new sample.
		
		:param float time: The time for this sample set (zero-based at start)
		:param ndarray Ts: The new temperature samples, size: (19, 1)
		:param ndarray Vs: The new voltage samples, size: (6, 1)
		:param ndarray As: The new current samples, size: (6, 1)
		:param float Ps: The new pressure sample
		:param bool redraw: True to redraw the plot, False otherwise
		"""
		# Roll the data backwards by one to insert new data at the end
		self._time_data = np.roll(self._time_data, -1)
		self.T_data = np.roll(self.T_data, -1, axis=0)
		self.V_data = np.roll(self.V_data, -1, axis=0)
		self.A_data = np.roll(self.A_data, -1, axis=0)
		self.P_data = np.roll(self.P_data, -1, axis=0)

		# Put the new data in the history arrays
		self._time_data[-1] = time / 60
		self.T_data[-1, :] = Ts
		self.V_data[-1, :] = Vs
		self.A_data[-1, :] = As
		self.P_data[-1, :] = Ps

		# Update the temperature lines
		for i, t_line in enumerate(self._T_lines):
			t_line[0].set_data(self._time_data, self.T_data[:, i])
			self._T_leg.texts[i].set_text(('{:<15}{:>7.3f} K').format(MonitorPlot._T_LABELS[i], self.T_data[:, i][-1]))

		# Update the voltage lines
		for i, v_line in enumerate(self._V_lines):
			v_line[0].set_data(self._time_data, self.V_data[:, i])
			self._V_leg.texts[i].set_text(('{:<15}{:>7.3f} V {:>7.3f} A').format(MonitorPlot._V_LABELS[i], self.V_data[:, i][-1], self.A_data[:, i][-1]))

		# Update the pressure data
		self._P_lines[0][0].set_data(self._time_data, self.P_data)
		self._P_leg.texts[0].set_text(('Pressure {:>7.3f} mbar').format(self.P_data[-1,0]))

		# Redraw the plot if requested
		if redraw:
			self._V_plot.set_xlim(self._time_data[0], self._time_data[-1] + self._sleep_minutes * 2)
			plt.draw()


	def wait(self, sleep_interval=None):
		"""
		Pauses the application for a set amount of time, while still allowing input on the plots
		
		:param float sleep_interval: The number of seconds to sleep, or None to use the time passed to the constructor
		"""
		plt.pause(sleep_interval if sleep_interval is not None else self._sleep)
