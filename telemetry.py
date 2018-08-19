#!/usr/bin/env python

import sys
import math
import time
import base_config
from state_machine import state_machine
import krpc
import curses
import signal
import numpy
from scipy.misc import derivative

numpy.seterr(all='ignore')

def handle_ctrlc(sig, frame):
  curses.endwin()
  sys.exit(0)
signal.signal(signal.SIGINT, handle_ctrlc)

# Set up the curses screen
stdscr = curses.initscr()
curses.curs_set(0)

def print_there(x, y, string):
  global stdscr
  stdscr.clrtoeol()
  stdscr.refresh()
  stdscr.addstr(y, x, string)
  stdscr.refresh()  

def f(x):
  return 25*numpy.log2(0.3*x)+90

def print_telem(v):
  flt = v.flight()
  downrange = ftl.longitude - initial_long
  proposed_angle = derivative(f, 1 + downrange)
  if proposed_angle > 90 or math.isnan(proposed_angle):
    proposed_angle = 90
  print_there(0, 1, "%f, %f" % (ftl.latitude, ftl.longitude))
  print_there(0, 2, "Altitude: %.2fm" % ftl.mean_altitude)
  print_there(0, 3, "%.2fg" % ftl.g_force)
  print_there(0, 4, "%sm/s (mach %.2f)" % (ftl.speed, ftl.mach))
  print_there(0, 5, "%.2fdeg pitch (%.2f commanded)" % (ftl.pitch, v.auto_pilot.target_pitch))
  print_there(0, 6, "%.2fdeg heading (%.2f commanded)" % (ftl.heading, v.auto_pilot.target_heading))
  print_there(0, 7, "%.2fQ" % ftl.dynamic_pressure)
  print_there(0, 8, "%fdeg down range" % downrange)
  print_there(0, 8, "Proposed command angle: %.2f" % proposed_angle)


# connect to kerbal and get the vehicle
conn = base_config.begin("telemetry")
vessel = conn.space_center.active_vessel
ftl = vessel.flight()

initial_long = ftl.longitude
# Main loop
while True:
  print_telem(vessel)
  time.sleep(0.5)

curses.endwin()
