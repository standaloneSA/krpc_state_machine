import math
import numpy
from scipy.misc import derivative

numpy.seterr(all='ignore')

def leo_normal_profile_log(x):
  """ Function to pass to scipi's derivative function """
  val = 32*numpy.log2(0.5*x)+90
  return val

def leo_steep_profile_log(x):
  """ Function to pass to scipi's derivative function """
  val = 35*numpy.log2(0.5*x)+90
  return val

def leo_shallow_profile_log(x):
  """ Function to pass to scipi's derivative function """
  val = 10*numpy.log2(x)+90
  return val

def leo_normal_profile(downrange, vehicle=None):
  return derivative(leo_normal_profile_log, 1 + downrange)

def leo_steep_profile(downrange, vehicle=None):
  return derivative(leo_steep_profile_log, 1 + downrange)

def leo_shallow_profile(downrange, vehicle=None):
  return derivative(leo_shalow_profile_log, 1 + downrange)

def gto_profile(downrange, vehicle=None):
  return derivative(leo_normal_profile_log, 1 + downrange)

def escape_profile(downrange, vehicle=None):
  return derivative(leo_steep_profile_log, 1 + downrange)

def prograde_profile(downrange, vehicle=None):
  pass

def retrograde_profile(downrange, vehicle=None):
  pass

def adaptive_profile(downrange, vehicle=None):
  """ 
    This profile determines whether the periapsis or apoapsis is closer to
    our current altitude, and then it attempts to keep us right on top of that
    by adjusting our pitch up and down, from -20.0 to 20.0 degrees. 
  """
  body = vehicle.orbit.body
  alt = vehicle.flight(body.reference_frame).surface_altitude
  apo_alt = vehicle.orbit.apoapsis_altitude
  peri_alt = vehicle.orbit.periapsis_altitude
  if abs(alt - apo_alt) < abs(alt - peri_alt):
    closest_node = vehicle.orbit.apoapsis_altitude
  else:
    closest_node = vehicle.orbit.periapsis_altitude

  dist = closest_node - alt
  if dist < -20.0:
    angle = -20.0
  elif dist > 20.0:
    angle = 20.0
  else:
    angle = dist
  return angle
