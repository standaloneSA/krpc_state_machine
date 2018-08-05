#!/usr/bin/env python

import os
import sys
import krpc
from ConfigParser import ConfigParser

version = 0.1 
cfg_file = "kvsw.config"
connect_name = "kVSW"

def begin(client=connect_name):
  """ Returns the krpc connection object """
  cf = ConfigParser()
  try:
    cf.readfp(open(cfg_file))
  except Exception:
    print("Error opening config file")
    sys.exit(1)

  try:
    server = cf.get("krpc", "server")
    port = int(cf.get("krpc", "port"))
    stream_port = port+1
  except Exception:
    print("Error reading the server from " + cfg_file + ". Is the format correct?")
    sys.exit(1)

  conn = krpc.connect(
    client + " " + str(version),
    address = server,
    rpc_port=port,
    stream_port=stream_port)

  return conn
  
def end(conn):
  """ Closes conection """
  conn.close()

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

