import math
import time
import numpy
from scipy.misc import derivative
from scipy.interpolate import interp1d
import launch_profiles

numpy.seterr(all='ignore')

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
  target_apoapsis = None
  target_periapsis = None
  ascent_profile = None
  initial_longitude = None
  mach_check = True


  profiles = {
    'leo_normal': launch_profiles.leo_normal_profile,
    'leo_steep': launch_profiles.leo_steep_profile,
    'gto': launch_profiles.gto_profile,
    'escape': launch_profiles.escape_profile
  }

  def __init__(self, conn):
    """ 
      Takes a state_machine object that has been initialized
      and a vehicle object from krpc that it can command
    """
    self.conn = conn
    self.vehicle = conn.space_center.active_vessel
    self._Flight = self.vehicle.flight()
    self.altitude = conn.add_stream(getattr, self.vehicle.flight(), 'mean_altitude')
    self.apoapsis = conn.add_stream(getattr, self.vehicle.orbit, 'apoapsis_altitude')
    self.initial_longitude = self.vehicle.flight().longitude

  def set_launch_profile(self, profile):
    """ Set the ascent profile so we know which equation to use """
    self.ascent_profile = self.profiles[profile]

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
    sas = str2bool(sas)

    """ Set whether sas is enabled """
    if sas:
      print("   Engaging SAS")
      self.vehicle.auto_pilot.engage()
      #self.vehicle.control.sas = True
    else:
      print("   Disengaging SAS")
      self.vehicle.control.sas = False
      self.vehicle.auto_pilot.disengage()

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
    #print("Target Pitch: " + str(self.vehicle.auto_pilot.target_pitch))
    if pitch == "follow_path":
      pass
    elif pitch == "keep":
      self.vehicle.auto_pilot.target_pitch = self.vehicle.flight().pitch
    else:
      self.vehicle.auto_pilot.target_pitch = float(pitch)

  def command_yaw(self, yaw):
    """ Controls the yaw of the vehicle """
    if yaw == "follow_path":
      pass
    elif yaw == "keep":
      self.vehicle.auto_pilot.target_yaw = self.vehicle.flight().yaw
    else:
      self.vehicle.auto_pilot.target_yaw = float(yaw)

  def command_roll(self, roll):
    """ Controls the roll of the vehicle """
    self.vehicle.auto_pilot.target_roll = float(roll)

  def command_heading(self, heading):
    """ 
      Controls the heading of the vehicle 
      Note: Until we get autopilot to work, we will have to 
      provide an absolute control input. 

      This will require some math. 
    """
    self.vehicle.auto_pilot.target_heading = float(heading)

  def self_destruct(self, destruct):
    """ Blow up the ship, presumably for safety reasons """
    pass

  def set_target_apoapsis(self, altitude):
    """ Set the target altitude for the apoapsis """
    self.target_apoapsis = float(altitude)

  def set_target_periapsis(self, altitude):
    """ Set the target altitude for the periapsis """
    self.target_periapsis = float(altitude)

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

  def mach_check(self, setting):
    """ Some flight regimes show up as hitting mach, but
        we don't want to consider them for transmach tests
    """
    self.mach_check = setting

  def is_transmach(self):
    """
       It is difficult to change direction during 
       transmach regimes, so we alert if so, to prevent
       the vehicle from potentially ripping itself apart. 
    """
    if self._Flight.mach > 0.8 and self._Flight.mach < 1.2:
      return True
    return False

  def update_engines(self):
    """ 
      This function is used to command the vehicle to a certain
      path. The way this happens is by evaluating an equation and 
      differentiating the result, then determing the angle to pitch
      over the rocket by. 
    """
    pass
    downrange = self.vehicle.flight().longitude - self.initial_longitude
    angle = self.ascent_profile(downrange)
    if angle > 90 or math.isnan(angle):
       angle = 90
    self.command_pitch(angle)

  def ready_for_state_change(self):
    """ See if we are hitting our targets """
    altitude = self.altitude()

    if self.target_altitude != None:
      if altitude >= (self.target_altitude * 1000):
        return self.next_state
    if self.target_apoapsis != None:
      if self.target_apoapsis <= self.vehicle.orbit.apoapsis_altitude:
        print("Met target apoapsis")
        self.target_apoapsis = None
        return self.next_state
    if self.target_periapsis != None:
      peri = self.vehicle.orbit.periapsis_altitude
      if (self.target_periapsis * 0.9) <= self.vehicle.orbit.periapsis_altitude <= (self.target_periapsis * 1.1):
        print("Met target periapsis")
        self.target_periapsis = None
        return self.next_state
    if self.vehicle.resources.amount('LiquidFuel') < 0.1 or self.vehicle.resources.amount('Oxidizer') < 0.1:
      return 'outta_gas'
    if self.target_speed != None:
      if self.mach_check: 
        if self.target_speed == "mach1":
          if self.is_transmach():
            return 'transsonic'  
    return False

