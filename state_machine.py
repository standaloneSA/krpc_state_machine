from ConfigParser import ConfigParser

class state_machine:
  """ 
  Representation of the state machine

  This file contains the functions that read the state machine config and 
  generates the transition functions.

  """
  state = None
  initial_state = None
  
  transition_map = {}
  abort_map = {}
  commands_map = {}
    
  def __init__(self):
    """ Read the config and set the initial transition map """
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

  def __str__(self):
    return self.state

  def trans(self, new_state):
    """ Verify that we can transition to the new state
    and then do so
    """
    if new_state in self.transition_map[self.state]:
      self.state = new_state 
      print(new_state)
    else:
      print("Unable to transition to " + new_state + ". Aborting.")
      self.abort() 
    
  def abort(self):
    """ Something has gone off the rails. Figure out our abort mode and
    to to it """
    self.trans(self.abort_map[self.state]) 
