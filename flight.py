
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

class Flight:
  """ The flight object that we use to issue commands """

  vehicle = None
  state_machine = None
  countdown = None
  state_timer = None
  next_state = None
  staging = False
  _Flight = None
  altitude = None
  apoapsis = None
  target_speed = None
  target_altitude = None

  def __init__(self, conn, vehicle):
    """ 
      Takes a state_machine object that has been initialized
      and a vehicle object from krpc that it can command
    """
    self.vehicle = vehicle
    self._Flight = self.vehicle.flight()
    self.altitude = conn.add_stream(getattr, vehicle.flight(), 'mean_altitude')
    self.apoapsis = conn.add_stream(getattr, vehicle.orbit, 'apoapsis_altitude')

  def launch_time(self, seconds):
    """ Update the countdown clock """
    self.countdown = seconds

  def time_in_state(self, seconds):
    """ Sets a timer to actually transition to next state """ 
    self.state_timer = seconds

  def following_state(self, next_state):
    """ If we have a timer, then when the timer expires, go here """
    self.next_state = next_state
     
  def command_stage(self, do_it):
    """ Activates staging for the vehicle """
    self.staging = str2bool(do_it)

  def enable_sas(self, sas):
    """ Set whether sas is enabled """
    #self.vehicle.control.sas = str2bool(sas)
    self.vehicle.auto_pilot.engage()

  def enable_rcs(self, rcs):
    """ Set whether RCS is enabled """
    self.vehicle.control.rcs = str2bool(rcs)

  def command_throttle(self, set_throttle):
    """ Throttle is provided in increments from 1 - 100 for 
        config file clarity. The game wants them in 0 - 1.0
    """
    self.vehicle.control.throttle = (float(set_throttle) * 0.01)

  def command_pitch(self, pitch):
    """ Controls the pitch of the vehicle """
    #if self.vehicle.control.auto_pilot.engaged:
    self.vehicle.auto_pilot.target_pitch = float(pitch)
    #else:
     # raise Exception("Error: non-autopilot is not supported")

  def command_heading(self, heading):
    """ Controls the heading of the vehicle """
    #if self.vehicle.control.sas:
    self.vehicle.auto_pilot.target_heading = float(heading)
    #else:
    #  raise Exception("Error: non-autopilot is not supported")

  def self_destruct(self, destruct):
    """ Blow up the ship, presumably for safety reasons """
    pass

  def set_target_altitude(self, altitude):
    """ Set the target altitude for this state """
    if altitude == "apoapis":
      self.target_altitude = self.apoapsis()
    elif altitude == "":
      self.target_altitude = None
    else:
      self.target_altitude = float(altitude)

  def set_target_speed(self, speed):
    """ Set the target speed for this state """
    self.target_speed = speed

  def is_transmach(self):
    if self._Flight.mach > 0.8 and self._Flight.mach < 1.2:
      return True
    return False

  def ready_for_state_change(self):
    """ See if we are hitting our targets """
    altitude = self.altitude()
    apoapsis = int(self.apoapsis())

    if self.target_altitude != None:
      if altitude >= (self.target_altitude * 1000):
        return self.next_state
    if self.target_speed != None:
      if self.target_speed == "mach1":
        if self.is_transmach():
          return 'transsonic'  
    return False
