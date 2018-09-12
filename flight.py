import math
import time
import numpy
from datetime import datetime, timedelta
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
  reentry_state = None
  staging = False
  _Flight = None

  # Are we in reentry? 
  reentry = False

  altitude = None
  apoapsis = None
  target_speed = None
  target_altitude = None
  target_apoapsis = None
  target_periapsis = None
  ascent_profile = None
  initial_longitude = None
  fairing_deploy = None
  engine_out_response_state = None
  mach_check_bool = True
  safe_orbit = False
  check_safe_orbit_bool = None
  chute_check_bool = False
  auto_pilot = False
  point_to_node = None

  profiles = {
    'leo_normal': launch_profiles.leo_normal_profile,
    'leo_steep': launch_profiles.leo_steep_profile,
    'gto': launch_profiles.gto_profile,
    'escape': launch_profiles.escape_profile,
    'adaptive': launch_profiles.adaptive_profile,
    'prograde': launch_profiles.prograde_profile,
    'retrograde': launch_profiles.retrograde_profile
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
    self.launch_time = datetime.now() + timedelta(0, float(seconds))
    self.countdown = seconds

  def time_in_state(self, seconds):
    """ Sets a timer to actually transition to next state """ 
    self.state_timer = seconds

  def set_tminus_zero(self, time=None):
    """ Sets the time for the launch timer """
    if time != "True":
      self.launch_time = time
    else:
      self.launch_time = datetime.now()

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
      self.vehicle.auto_pilot.engage()
      self.auto_pilot = True
      #self.vehicle.control.sas = True
    else:
      self.vehicle.control.sas = False
      self.vehicle.auto_pilot.disengage()
      self.auto_pilot = False

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
    self.point_to_node = None
    if pitch == "follow_path":
      pass
    elif pitch == "prograde":
      if self.auto_pilot:
        self.vehicle.auto_pilot.target_direction = self.vehicle.flight().prograde
    elif pitch == "retrograde":
      if self.auto_pilot:
        self.vehicle.auto_pilot.target_direction = self.vehicle.flight().retrograde
    elif pitch == "keep":
      if self.auto_pilot:
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
    if altitude == "None":
      self.target_apoapsis = None
    else:
      self.target_apoapsis = float(altitude)

  def set_target_periapsis(self, altitude):
    """ Set the target altitude for the periapsis """
    self.target_periapsis = float(altitude)

  def set_target_altitude(self, altitude):
    """ Set the target altitude for this state """
    if altitude == "None":
       self.target_altitude = None
    elif altitude == "apoapsis":
      self.target_altitude = self.apoapsis()
    elif altitude == "":
      self.target_altitude = None
    else:
      self.target_altitude = float(altitude)

  def set_target_speed(self, speed):
    """ Set the target speed for this state """
    self.target_speed = speed

  def set_reentry_state(self, state):
    """
      Various spacecraft may care about re-entering the atmosphere. Things
      like landing rockets, capsules, and maybe asteroids. This method
      will allow us to change the state to whatever the given re-entry state
      is. This state transition is triggered by being above the atmosphere 
      and then going down to the atmosphere boundry for whatever the current
      sphere of influence is.
    """
    self.reentry_state = state

  def is_reentry(self):
    """ Check if we are in reentry. Qualifications are: 
      - At the atmospheric transition boundry for the current sphere of influence
      - Headed in a downward trajectory
    """
    if not self.reentry:
      if self.vehicle.orbit.body.has_atmosphere:
        body = self.vehicle.orbit.body
        body_atmo = body.atmosphere_depth
        our_altitude = self.vehicle.flight(body.reference_frame).surface_altitude
        if self.vehicle.flight(body.reference_frame).vertical_speed < 0:
          # going down
          if abs(body.atmosphere_depth - our_altitude) < 100:
            self.reentry = True
            return True
    return False 
      
  def mach_check(self, setting):
    """ Some flight regimes show up as hitting mach, but
        we don't want to consider them for transmach tests
    """
    self.mach_check_bool = str2bool(setting)

  def is_transmach(self):
    """
       It is difficult to change direction during 
       transmach regimes, so we alert if so, to prevent
       the vehicle from potentially ripping itself apart. 
    """
    if self._Flight.mach > 0.8 and self._Flight.mach < 1.2:
      return True
    return False

  def fairing_sep(self, altitude):
    """ Set the altitude for fairing deploy """
    self.fairing_deploy = altitude

  def deploy_payload(self, value):
    """ We assume that the next decoupler is a payload despensor
        and so we trigger it to releaes a payload. We only do one
        in case we are releasing a constellation, so we can do
        this many times 
    """
    if str2bool(value):
      print(" *** Deploying payload")
      self.vehicle.parts.decouplers[0].decouple()

  def activate_engine(self, engine):
    """ After staging, engines may be manually activated """
    self.vehicle.parts.engines[0].active = True

  def engine_out_response(self, state):
    """ What do we do if we encounter engine.has_fuel = False """
    self.engine_out_response_state = state

  def deploy_chutes(self):
    """ Throw the chutes and hope for the best """
    for chute in self.vehicle.parts.parachutes:
      if not chute.deployed:
        print(" *** Deploying parachute")
        chute.deploy()

  def verify_safe_orbit(self, value):
    """ Set the bool as to whether we should check for a safe orbit """
    self.check_safe_orbit_bool = str2bool(value)

  def check_safe_orbit(self):
    """ A safe orbit is one where we are not going to re-enter the atmosphere """
    pass
    body = self.vehicle.orbit.body
    body_atmo = body.atmosphere_depth
    if self.vehicle.orbit.periapsis_altitude > body_atmo and self.vehicle.orbit.apoapsis_altitude > body_atmo:
      return True
    return False

  def check_for_chute_deploy(self, value):
     if str2bool(value):
       print("Should be checking for chute deploy")
       self.chute_check_bool = True

  def update_engines(self):
    """ 
      This function is used to command the vehicle to a certain
      path. The way this happens is by evaluating an equation and 
      differentiating the result, then determing the angle to pitch
      over the rocket by. 
    """
    downrange = self.vehicle.flight().longitude - self.initial_longitude
    # The magic of this next line is that self.ascent_profile is equivalent
    # to a function. 
    angle = self.ascent_profile(downrange, self.vehicle)
    if angle > 90 or math.isnan(angle):
       angle = "keep"
    self.command_pitch(angle)

  def ready_for_state_change(self):
    """ See if we are hitting our targets """
    altitude = self.altitude()

    if self.fairing_deploy:
      if altitude >= float(self.fairing_deploy):
        self.fairing_deploy = False
        print("  *** Deploying fairing")

        # This won't work for more complicated vehicle setups, but it is
        # simplistic enough to start with. 
        for fairing in self.vehicle.parts.fairings:
          fairing.jettison()
    if self.engine_out_response_state:
      for engine in self.vehicle.parts.engines:
        if not engine.has_fuel:
          print ("  *** Engine fuel depeleted")
          self.next_state = self.engine_out_response_state
          self.engine_out_response_state = None
          print("returning 1 %s" % self.next_state)
          return self.next_state
    if self.check_safe_orbit_bool:
      self.safe_orbit = self.check_safe_orbit()
    if self.target_altitude != None:
      if altitude >= self.target_altitude:
        print("  *** Target altitude hit")
        print("returning 2 %s" % self.next_state)
        return self.next_state
    if self.target_apoapsis != None:
      if self.target_apoapsis <= self.vehicle.orbit.apoapsis_altitude:
        print("  *** Met target apoapsis")
        self.target_apoapsis = None
        print("returning 3 %s" % self.next_state)
        return self.next_state
    if self.target_periapsis != None:
      peri = self.vehicle.orbit.periapsis_altitude
      if (self.target_periapsis * 0.95) <= self.vehicle.orbit.periapsis_altitude <= (self.target_periapsis * 1.05):
        print("  *** Met target periapsis")
        self.target_periapsis = None
        print("returning 4 %s" % self.next_state)
        return self.next_state
    if (self.vehicle.resources.amount('LiquidFuel') < 0.1 and self.vehicle.resources.max('LiquidFuel') > 0.0) or (self.vehicle.resources.amount('Oxidizer') < 0.1 and self.vehicle.resources.max('Oxidizer') > 0.0):
      print("returning 5 %s" % self.engine_out_response_state)
      return self.engine_out_response_state
    if self.chute_check_bool:
      chute_check_notify = True
      if self.reentry:
        # If the pressure on the vehicle is okay for the chutes, go for it
        # Note: We don't support things like drogue chutes yet. We just deploy
        # the whole kit and kaboodle
        if self.vehicle.flight().static_pressure > self.vehicle.parts.parachutes[0].deploy_min_pressure:
          self.deploy_chutes()
    if self.reentry_state != None:
      if self.is_reentry():
        print("  *** Entering atmosphere. Transitioning to %s" + self.reentry_state)
        return self.reentry_state
    if self.target_speed != None:
      if self.mach_check_bool: 
        if self.target_speed == "mach1":
          if self.is_transmach():
            print("  *** Entering transsonic regime")
            return 'transsonic'  
    return False

