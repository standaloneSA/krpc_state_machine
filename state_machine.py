import sys
from ConfigParser import ConfigParser
from flight import Flight
import threading

class state_machine:
  """ 
  Representation of the state machine

  This file contains the functions that read the state machine config and 
  generates the transition functions.

  """
  state = None
  initial_state = None
  flight = None
  vehicle = None
  conn = None
  
  transition_map = {}
  abort_map = {}
  commands_map = {}
  
  abort_counter = 0
    
  def __init__(self, conn, vehicle):
    """ Read the config and set the initial transition map """

    self.conn = conn
    state_cfgfile = "configs/states_transitions"
    state_commands_cfgfile = "configs/states_command"

    state_config = ConfigParser()
    state_config.readfp(open(state_cfgfile))

    state_commands_config = ConfigParser()
    state_commands_config.readfp(open(state_commands_cfgfile))

    states = state_config.sections()
    for state in states:
      transitions = state_config.get(state, 'transitions').split(",")

      self.abort_map[state] = state_config.get(state, 'abort')
      self.transition_map[state] = transitions

      self.commands_map[state] = state_commands_config.items(state)
      try:
        is_initial_state = state_config.get(state, 'initial_state')
        if is_initial_state:
          self.initial_state = state
      except Exception:
        pass
    self.state = self.initial_state
    self.flight = Flight(conn, vehicle)
    self.vehicle = vehicle

  def __str__(self):
    return self.state

  def trans(self, new_state):
    """ Verify that we can transition to the new state
    and then do so
    """
    if new_state == self.state:
       return 

    if new_state in self.transition_map[self.state]:
      self.state = new_state 
      print("")
      print("[" + new_state + "]")
      self.conn.ui.message("[" + new_state + "]", duration=5.0)

      # Some stages before launch require timing rather than flight
      # checks. In those cases, we need to start a timer to trans
      # between stages, rather than check flight characteristics. 
      timed_state = False
      time_in_state = None
      next_state = None
      for command, value in self.commands_map[self.state]:
        # Issue commands to vehicle and perform staging.
        print(" - " + str(command) + " / " + str(value))
        getattr(self.flight, command)(value)
        if command == "time_in_state":
          timed_state = True
          time_in_state = int(value)
        if command == 'following_state':
          next_state = value 
      if self.flight.staging:
        self.vehicle.control.activate_next_stage()
      print(" - Timed state: " + str(timed_state))
      if timed_state:
        pass
        timer = threading.Timer(time_in_state, self.trans, args=[next_state])
        timer.start()
    else:
      print("Unable to transition to " + new_state + ". Aborting.")
      self.abort() 

  def abort(self):
    """ Something has gone off the rails. Figure out our abort mode and
    to to it """
    self.abort_counter += 1
    if self.abort_counter > 5:
      sys.exit(1)
    self.trans(self.abort_map[self.state]) 
