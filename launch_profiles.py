import math
import numpy
from scipy.misc import derivative

numpy.seterr(all='ignore')

def leo_normal_profile_log(x):
  """ Function to pass to scipi's derivative function """
  val = 35*numpy.log2(0.5*x)+90
  return val

def leo_normal_profile(downrange):
  return derivative(leo_normal_profile_log, 1 + downrange)

def leo_steep_profile(downrange):
  return derivative(leo_normal_profile_log, 1 + downrange)

def gto_profile(downrange):
  return derivative(leo_normal_profile_log, 1 + downrange)

def escape_profile(downrange):
  return derivative(leo_normal_profile_log, 1 + downrange)

