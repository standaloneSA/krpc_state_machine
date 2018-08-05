#!/usr/bin/env python

import sys
import math
import time
import base_config
from state_machine import state_machine
import krpc
import curses
import signal

def handle_ctrlc(sig, frame):
  curses.endwin()
  sys.exit(0)
signal.signal(signal.SIGINT, handle_ctrlc)

# Set up the curses screen
stdscr = curses.initscr()
curses.curs_set(0)

def print_there(x, y, string):
  global stdscr
  stdscr.addstr(y, x, string)
  stdscr.refresh()  

def print_telem(ftl):
  print_there(0, 1, "%f, %f" % (ftl.latitude, ftl.longitude))
  print_there(0, 2, "Altitude: %.2fm" % ftl.mean_altitude)
  print_there(0, 3, "%.2fg" % ftl.g_force)
  print_there(0, 4, "%sm/s (mach %.2f)" % (ftl.speed, ftl.mach))
  print_there(0, 5, "%sdeg pitch" % ftl.pitch)
  print_there(0, 6, "%sdeg heading" % ftl.heading)
  print_there(0, 7, "%.2fQ" % ftl.dynamic_pressure)



# connect to kerbal and get the vehicle
conn = base_config.begin()
vessel = conn.space_center.active_vessel
ftl = vessel.flight()


# Main loop
while True:
  print_telem(ftl)
  time.sleep(0.5)

curses.endwin()
