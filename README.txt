White Cryo Code


FRIDGE CYCLE:
  cooldown.py -Initial fridge cycle, start after reassembling cryo. To be run before fridge_cycle.py
  fride_cycle.py -Normal fridge cycle, edited to work with functions.py, menu to toggle ADR switch.
  fridge_cycle_ADRoff.py -Fridge cycle with ADR switch off, He-3 cycle is 2x normal (obsolete)
  power_supply.py -remote controller for the power switches for the ADR, He4, He3, switches and pumps.
  functions.py -driver for cycle and monitoring functions, contains instrument reading scripts

ADR:
  ADR.py -Automated script w/ GUI for AMI controller to cool down to a desired temp.
  ADRcontroller.py -GUI that allows remote controll of the AMI.

FRIDGE MONITORING:
  monitor_all.py - monitors and writes to file: temp. power and pressure
  monitor_TP.py - monitors and writes to file: temp and power.

PLOTTING:
  plot.py - plots temperature and voltage with command line interface, has checkbutton GUI for selecting visible plots

BLACKBODY:
  blackbody.py - plots only black body data and fits an exponential curve

#old files are now in Archive
#Please read readme's in individual scripts for furthur info.
