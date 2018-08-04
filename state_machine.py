
class state_machine:
  """ 
  Representation of the state machine

  This file contains the functions that read the state machine config and 
  generates the transition functions.

  """
  
  transition_map = {}
  abort_map = {}
  state = None
  initial_state = None
    
  def __init__(self, state_cfgfile):
    """ Read the config and set the initial transition map """
    from ConfigParser import ConfigParser
    cf = ConfigParser()
    cf.readfp(open(state_cfgfile))
    states = cf.sections()
    for state in states:
      transitions = cf.get(state, 'transitions').split(",")
      self.abort_map[state] = cf.get(state, 'abort')
      self.transition_map[state] = transitions
      try:
        is_initial_state = cf.get(state, 'initial_state')
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
