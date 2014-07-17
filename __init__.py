#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import psutil
import time

from collections import namedtuple

import helpers

def get_time():
    """ Unified/comparable clock access """
    return time.time()


## XXX for interactive debugging only
def RELOAD():
    print ("import importlib")
    print ("importlib.reload(cpunetlog)")


MEASUREMENT_INTERVAL = 0.2



class Reading:
    ## XXX DEPRECATED
    last_measurement = None

    @classmethod
    def get_time_since_last_measurement(cls):
        """ Time since last measurement in seconds (float) """
        assert( Reading.last_measurement )
        return Reading.get_time() - Reading.last_measurement

    @staticmethod
    def update_last_measurement(t):
        Reading.last_measurement = t

    ## XXX DEPRECATED
    ## Exceptions
    class TaintedResultsException(Exception):
        pass


    ## ***
    def __init__(self):
        ## sanity check  ## XXX DEPRECATED
        if ( self.last_measurement ):
            if ( get_time() - self.last_measurement < 0.09 ):
                print( "WARN: time diff only:", get_time() - self.last_measurement )
                raise self.TaintedResultsException

        ## * measurements *
        self.timestamp = get_time()
        self.cpu_util = psutil.cpu_percent(interval=0, percpu=True)                      ## XXX
        self.cpu_times_percent = psutil.cpu_times_percent(interval=0, percpu=True)       ## XXX
        self.cpu_times = psutil.cpu_times(percpu=True)
        self.memory = psutil.virtual_memory()
        self.net_io = psutil.net_io_counters(pernic=True)

        ## store timespan for these statistics (if reasonable)  ## XXX DEPRECATED
        if ( self.last_measurement ):
            self.timespan = self.timestamp - self.last_measurement
            self.valid = True
        else:
            self.timespan = None
            self.valid = False

        ## update class variable
        self.update_last_measurement(self.timestamp)

    def __str__(self):
        ## •‣∘⁕∗◘☉☀★◾☞☛⦿
        return "◘ Timespan: " + str(self.timespan) +              \
                "\n◘ CPU utilization: " + str(self.cpu_util) +    \
                "\n◘ CPU times: " + str(self.cpu_times) +         \
                "\n◘ RAM: " + str(self.memory) +                  \
                "\n◘ NET: " + str(self.net_io)



class NetworkTraffic:
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
    def __init__(self, reading1, reading2):
        self.r1 = reading1
        self.r2 = reading2

        ## calculate differences
        self.timespan = self.r2.timestamp - self.r1.timestamp
        self.cpu_times_percent = helpers.calculate_cpu_times_percent(self.r1.cpu_times, self.r2.cpu_times, percpu=True)
        #self.net_io_diff = helpers.calculate_element_diffs_for_dict_of_tuples(self.r1.net_io, self.r2.net_io)
        #self.net_io_rate = self._calculate_net_io_rate()
        self.net_io = self._calculate_net_io()


    def _calculate_net_io(self):
        ret = dict()

        for nic in self.r1.net_io.keys():
            ret[nic] = NetworkTraffic(self.r1.net_io[nic], self.r2.net_io[nic], self.timespan)

        return ret


    #def __str__(self):
        #return str(self.timespan) + ", " + str(self.r2.timespan)   ## XXX
        #return str(self.cpu_times_percent) + "\n" + str(self.r2.cpu_times_percent)   ## XXX


def measure(interval = MEASUREMENT_INTERVAL):
    r1 = Reading()
    time.sleep(interval)
    r2 = Reading()

    m = Measurement(r1, r2)

    return m



def display(measurement):
    nic = "eth0"

    for cpu in measurement.cpu_times_percent:
        print( ", ".join([str(x) + "%" for x in cpu]))
        print( str(100-cpu.idle) + "%, " + str(cpu.user) + "%. " + str(cpu.system) + "%")
    for nic in measurement.net_io.keys():
        print( "[" + nic + "] " + str(measurement.net_io[nic]) )

    print


## Takes a reading and ensures that (at least) |interval| seconds are covered.
#    NOTE: does not handle race conditions (well)
def take_reading(interval = MEASUREMENT_INTERVAL):
    t = interval - Reading.get_time_since_last_measurement()

    ## sleep if necessary
    if ( t > 0 ):
        time.sleep(t)

    m = Reading()
    assert(m.timespan >= interval)

    return m


## XXX TESTING
def test_loop():
    for i in range(10):
        m = take_reading(0.5)
        display( m )


## XXX TESTING
display( measure() )


