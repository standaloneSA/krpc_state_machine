#!/usr/bin/env python

import sys
import signal
from base_config import str2bool
import base_config
from state_machine import state_machine

def handle_ctrlc(sig, frame):
  sm.abort()
  sys.exit(0)

signal.signal(signal.SIGINT, handle_ctrlc)

conn = base_config.begin()

sm = state_machine(conn, conn.space_center.active_vessel)

# Add the callback to trigger abort from in-game
abort = conn.add_stream(getattr, sm.vehicle.control, 'abort')
abort.add_callback(sm.abort)
abort.start()

sm.trans('pre_hold')

while sm.state != "abort":
  next_state = sm.flight.ready_for_state_change()
  if next_state:
    sm.trans(next_state)


