#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import psutil
import time


## XXX for interactive debugging only
def RELOAD():
    print ("import importlib")
    print ("importlib.reload(cpunetlog)")


MEASUREMENT_INTERVAL = 0.2

class Measurement:
    last_measurement = None

    @staticmethod
    def get_time():
        """ Unified/comparable clock access """
        return time.time()

    @classmethod
    def get_time_since_last_measurement(cls):
        """ Time since last measurement in seconds (float) """
        assert( cls.last_measurement )
        return cls.get_time() - cls.last_measurement

    @classmethod
    def update_last_measurement(cls, t):
        cls.last_measurement = t

    ## Exceptions
    class TaintedResultsException(Exception):
        pass


    ## ***
    def __init__(self):
        ## sanity check
        if ( self.last_measurement ):
            if ( self.get_time() - self.last_measurement < 0.09 ):
                raise self.TaintedResultsException

        ## timing
        t = self.get_time()

        ## * measurements *
        self.cpu_util = psutil.cpu_percent(interval=0, percpu=True)
        self.cpu_times = psutil.cpu_times_percent(interval=0, percpu=True)
        self.memory = psutil.virtual_memory()
        self.net_io = psutil.net_io_counters(pernic=True)

        ## timing
        t2 = time.time()
        assert( t2-t < 0.01 )   ## XXX should be fast!!

        ## store timespan for these statistics (if reasonable)
        if ( self.last_measurement ):
            self.timespan = t - self.last_measurement
            self.valid = True
        else:
            self.timespan = None
            self.valid = False

        ## update class variable
        self.update_last_measurement(t)

    def __str__(self):
        ## •‣∘⁕∗◘☉☀★◾☞☛⦿
        return "◘ Timespan: " + str(self.timespan) +              \
                "\n◘ CPU utilization: " + str(self.cpu_util) +    \
                "\n◘ CPU times: " + str(self.cpu_times) +         \
                "\n◘ RAM: " + str(self.memory) +                  \
                "\n◘ NET: " + str(self.net_io)


## TODO: debug and extend
class NiceMeasurement(Measurement):
    def __str__(self):
        return ", ".join([str(x) + "%" for x in self.cpu_util])


## Take a first (invalid) reading to initialize the system.
init_measure = Measurement()

## Takes a reading and ensures that (at least) |interval| seconds are covered.
#    NOTE: does not handle race conditions (well)
def take_reading(interval = MEASUREMENT_INTERVAL):
    t = interval - Measurement.get_time_since_last_measurement()

    ## sleep if necessary
    if ( t > 0 ):
        time.sleep(t)

    m = NiceMeasurement()
    assert(m.timespan >= interval)

    return m


## XXX TESTING
def test_loop():
    for i in range(10):
        m = take_reading(0.5)
        print( m )



## XXX TESTING
#print( take_reading() )


