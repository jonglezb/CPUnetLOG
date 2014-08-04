#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import psutil
import time
import sys
import traceback

from collections import namedtuple

import helpers
import curses_display as ui

def get_time():
    """ Unified/comparable clock access """
    return time.time()


## XXX for interactive debugging only
def RELOAD():
    print ("import importlib")
    print ("importlib.reload(cpunetlog)")


MEASUREMENT_INTERVAL = 0.2

nic_speeds = helpers.get_nic_speeds()


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
        self.cpu_times_percent = helpers.calculate_cpu_times_percent(self.r1.cpu_times, self.r2.cpu_times, percpu=True)
        self.net_io = self._calculate_net_io()


    def _calculate_net_io(self):
        ret = dict()

        for nic in self.r1.net_io.keys():
            ret[nic] = NetworkTraffic(self.r1.net_io[nic], self.r2.net_io[nic], self.timespan)

        return ret



def measure(interval = MEASUREMENT_INTERVAL):
    """ Convenience function to perform one »Measurement« """

    r1 = Reading()
    time.sleep(interval)
    r2 = Reading()

    m = Measurement(r1, r2)

    return m




## XXX TESTING -- NOTE: takes unnecessary Readings!!
def test_loop():
    err = None

    try:
        ui.init()
        ui.nics = nic_speeds.keys()
        ui.nic_speeds = nic_speeds

        while ui.display( measure(1.0) ):
            pass

    except KeyboardInterrupt:
        pass
    except Exception as e:
        err = e
        exc_type, exc_value, exc_traceback = sys.exc_info()
    finally:
        ui.close()

    ## On error: Print error message *after* curses has quit.
    if ( err ):
        print( "Unexpected exception happened: '" + str(err) + "'" )
        print

        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

        print
        print( "QUIT." )


## XXX TESTING
#display( measure() )
test_loop()

