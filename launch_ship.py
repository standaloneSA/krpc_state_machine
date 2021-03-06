#!/usr/bin/env python

import sys
import signal
import atexit
from base_config import str2bool
import base_config
from state_machine import state_machine
import time

print(chr(27)+'[2j')
print('\033c')
print('\x1bc')


def abort():
  sm.abort()
  sys.exit(0)

def handle_ctrlc(sig, frame):
  sm.abort()
  sys.exit(0)


signal.signal(signal.SIGINT, handle_ctrlc)
atexit.register(abort)

#config = "single_stage_leo"
#config = "two_stage_leo"
config = "kerbalx"

conn = base_config.begin()
sm = state_machine(conn, conn.space_center.active_vessel, "configs/" + config)

# Add the callback to trigger abort from in-game
abort = conn.add_stream(getattr, sm.vehicle.control, 'abort')
abort.add_callback(sm.abort)
abort.start()

print("Beginning launch with %s config" % config)
sm.trans('pre_hold')
while sm.state != "abort":
  next_state = sm.flight.ready_for_state_change()
  if next_state:
    print("Transitioning to %s" % next_state)
    sm.trans(next_state)
  if sm.engines_need_update:
    sm.flight.update_engines()  


