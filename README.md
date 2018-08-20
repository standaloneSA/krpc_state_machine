KRPC State Machine
==================

# What is KRPC State Machine?

KRPC State Machine is a framework for using [kRPC](https://github.com/krpc/krpc) to control vehicles. It uses configuration files and a flight class to limit what commands are available to a vehicle at any given time. 

# What is a state machine, and why would I use it?
A state machine (or [finite state machine](https://brilliant.org/wiki/finite-state-machines/)) is a way to build and control what programming something can run at any given time. 

This is important because there are times when you want to make sure something doesn't happen. For instance, if you have a rocket, you want to make sure that it doesn't jettison the fairings when it's on the launch pad. If that happens, you don't go to space today. (Well, it's Kerbal, so you could probably still make it work, but you know...) So what a state machine allows you to do is to say, 'When the rocket is on the launch pad, there is no way to even call the code that jettisons the fairings'. Not that you're not callin the code, but that, unless you specifically tell the fairings to jettison, that code can't be called. Also, you can specify that from the 'safe on the launchpad' state, you can ONLY transition to the right states. This means that you CAN transfer from 'safe on the pad' to 'go for launch', but not to 'payload deploy'. 

In 2013, Joshua A Harris and Ann Patterson-Hine published a research paper on [State machine modeing of the Space Launch System Solid Rocket Boosters](https://ti.arc.nasa.gov/publications/10841/download/)(PDF download). In the paper, they discussed how the SLS booster behavior could be described by finite state machines. 

This software is my personal effort to see this kind of thing in Kerbal. 

# How do I use this?

This is still under active development, so the details in the files will change over time, but generally, there are a few important files and directories: 

 - configs/
          mission1/
          mission2/
          ...etc...

The configs directory holds per-mission configs. The 'single_stage_leo' subdirectory is the simplest mission. If you have a single stage rocket that is capable of going to orbit (with no payload), then this should fly your mission into a 120km circular orbit.

Each mission consists of two files (in python ConfigParser format): 'states_command' and 'states_transisions'. 

states_transitions is the configuration file that limits which states the rocket can move to from whatever state it currently exists in.

states_command is a list of all of the different states that a rocket can be in (for this mission - remember, it's per-mission), and the commands that the rocket should execute when it transitions into those, and also settings for the rocket when it is in that state. If you look through the example above, you'll see pre_hold, startup, ignition, launch, and so on. 

The commands in states_command are actually methods that live in the flight class, in flight.py in the main directory. The idea is to not customize the flight.py file for a specific mission, but to write abstracted methods that can be called from the configuration file with values that make sense for the mission. 

Because the flight.py file is used by all missions, regardless of configuration file, it is very important to not break functionality for older missions. In the future, I will be building a test harness system that can run older flights against new changes to the code to ensure that there aren't regressions from changes. 

The actual state machine enforcement is done with the state machine class in state_machine.py. It should almost never be edited, because it is very generic. 
