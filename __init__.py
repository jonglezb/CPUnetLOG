#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Copyright (c) 2014,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# This code is provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock


import os
import psutil
import time
import sys
import traceback
import math
import json

from collections import namedtuple

import helpers
import curses_display as ui
from logging import LoggingManager
from psutil_functions import calculate_cpu_times_percent


def get_time():
    """ Unified/comparable clock access """
    return time.time()


## XXX for interactive debugging only
def RELOAD():
    print ("import importlib")
    print ("importlib.reload(cpunetlog)")


MEASUREMENT_INTERVAL = 0.2

nic_speeds = helpers.get_nic_speeds()
nics = list( nic_speeds.keys() )


class Reading:
    """ A single reading of various CPU, NET, ... values. --> Building block for the »Measurement« class."""

    def __init__(self):
        ## * measurements *
        self.timestamp = get_time()
        #self.cpu_util = psutil.cpu_percent(interval=0, percpu=True)                      ## XXX
        #self.cpu_times_percent = psutil.cpu_times_percent(interval=0, percpu=True)       ## XXX
        self.cpu_times = psutil.cpu_times(percpu=True)
        self.memory = psutil.virtual_memory()
        self.net_io = psutil.net_io_counters(pernic=True)
        self.nb_open_files = helpers.get_nb_open_files()

    def __str__(self):
        ## •‣∘⁕∗◘☉☀★◾☞☛⦿
        return "◘ Timespan: " + str(self.timespan) +              \
                "\n◘ CPU utilization: " + str(self.cpu_util) +    \
                "\n◘ CPU times: " + str(self.cpu_times) +         \
                "\n◘ RAM: " + str(self.memory) +                  \
                "\n◘ NET: " + str(self.net_io)



class NetworkTraffic:
    """ Utility class for calculating and storing network traffic: Total amount (during a timespan) and ratio. """

    def __init__(self, older_counters, younger_counters, timespan):
        self.total = dict()
        self.ratio = dict()

        for field in older_counters._fields:
            field_delta = getattr(younger_counters, field) - getattr(older_counters, field)

            self.total[field] = field_delta
            self.ratio[field] = field_delta / timespan

    def __str__(self):
        return "Total (bytes):" + str(self.total) + "; Ratio (bytes/s)" + str(self.ratio)



class Measurement:
    """ Calculates and stores CPU utilization, network traffic, ... during a timespan. Based two »Readings«. """

    def __init__(self, reading1, reading2):
        self.r1 = reading1
        self.r2 = reading2

        ## calculate differences
        self.timespan = self.r2.timestamp - self.r1.timestamp
        self.cpu_times_percent = calculate_cpu_times_percent(self.r1.cpu_times, self.r2.cpu_times, percpu=True)
        self.net_io = self._calculate_net_io()
        # Point measurement are measured at a given point in time, not during a timespan.  We use the second reading.
        self.memory = self.r2.memory
        self.nb_open_files = self.r2.nb_open_files


    def _calculate_net_io(self):
        ret = dict()

        for nic in self.r1.net_io.keys():
            ret[nic] = NetworkTraffic(self.r1.net_io[nic], self.r2.net_io[nic], self.timespan)

        return ret

    def get_begin(self):
        return self.r1.timestamp

    def get_end(self):
        return self.r2.timestamp



def measure(interval = MEASUREMENT_INTERVAL):
    """ Convenience function to perform one »Measurement« """

    r1 = Reading()
    time.sleep(interval)
    r2 = Reading()

    m = Measurement(r1, r2)

    return m




def main_loop():
    """ Main Loop:
      - Sets up curses-display
      - Takes a reading every second
      - Displays the measurements
      - Logs the measurements with the LoggingManager
    """

    ## TODO this should be configurable by command line options
    sample_interval = float(args.interval)
    display_interval = float(args.displayinterval)

    display_skip = max(display_interval / sample_interval, 1)

    err = None

    try:
        # Set up (curses) UI.
        ui.nics = nics
        ui.nic_speeds = nic_speeds
        ui.logging_manager = logging_manager
        if not args.headless:
            ui.init()

        # Take an initial reading.
        old_reading = Reading()

        # Sleep till the next "full" second begins. (In order to roughly synchronize with other instances.)
        now = time.time()
        time.sleep(math.ceil(now)-now)

        display_skip_counter = 0
        running = True
        while running:
            # Take a new reading.
            new_reading = Reading()

            # Calculate the measurement from the last two readings.
            measurement = Measurement(old_reading, new_reading)

            # Display/log the measurement.
            running &= logging_manager.log(measurement)
            if ( display_skip_counter % display_skip < 1 ) and not args.headless:   # the display may skip some samples
                running = ui.display( measurement )
                display_skip_counter = 0
            display_skip_counter += 1

            # Store the last reading as |old_reading|.
            old_reading = new_reading

            time.sleep(sample_interval)
                ## XXX TODO We could calculating the remaining waiting-time here.



    except KeyboardInterrupt:
        # Quit gracefully on Ctrl-C
        pass
    except Exception as e:
        # On error: Store stack trace for later processing.
        err = e
        exc_type, exc_value, exc_traceback = sys.exc_info()
    finally:
        # Tear down the UI.
        if not args.headless:
            ui.close()
        logging_manager.close()

    ## On error: Print error message *after* curses has quit.
    if ( err ):
        print( "Unexpected exception happened: '" + str(err) + "'" )
        print

        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

        print
        print( "QUIT." )




## MAIN ##
if __name__ == "__main__":

    ## Command line arguments
    import argparse
#
    parser = argparse.ArgumentParser()

    ## Logging
    parser.add_argument("-l", "--logging", action="store_true",
                        help="Enables logging.")
    parser.add_argument("-A", "--autologging", action="store_true",
                        help="Enables auto-logging. (Log only on network activity. Implies --logging)")
    parser.add_argument("-W", "--watch",
                        help="Store the command-line of the given program as log-comment. (Use together with --autologging.)")
    parser.add_argument("-c", "--comment",
                        help="A comment that is stored in the logfile. (See --logging.)")
    parser.add_argument("--path", default="/tmp/cpunetlog",
                        help="Path where the log files are stored in. (See --logging.)")
    parser.add_argument("--stdout", action="store_true",
                        help="Log to stdout instead of writing to a file (implies --logging and --headless, ignores --path)")
    parser.add_argument("-e", "--environment",
                        help="JSON file that holds arbitrary environment context. (This can be seen as a structured comment field.)")
    parser.add_argument("-i", "--interval", default="0.5",
                        help="Time between two samples (in seconds). [Default = 0.5]")
    parser.add_argument("-d", "--displayinterval", default="1",
                        help="Time between two display updates (in seconds). [Default = 1]")


    # NICs
    parser.add_argument("--nics", nargs='+',
                        help="The network interfaces that should be displayed (and logged, see --logging).")

    parser.add_argument("-q", "--headless", action="store_true", 
                        help="Run in quiet/headless mode without GUI")

    args = parser.parse_args()



    ## NICs
    monitored_nics = nics
    if ( args.nics ):
        #assert( set(nics).issuperset(args.nics) )
        monitored_nics = args.nics

    ## --autologging implies --logging
    if ( args.autologging ):
        args.logging = True

    ## --stdout implies --logging and --headless
    if args.stdout:
        args.logging = True
        args.headless = True
        # By convention, path == None means "output to stdout"
        args.path = None

    ## compensate psutil version incompatibilities
    try:
        num_cpus = psutil.cpu_count()
    except:
        num_cpus = psutil.NUM_CPUS

    ## Logging
    logging_manager = LoggingManager( num_cpus, monitored_nics, helpers.get_sysinfo(), args.environment,
                                      args.comment, args.path, args.autologging, args.watch )
    if args.logging:
        logging_manager.enable_measurement_logger()


    # Run the main loop.
    main_loop()

