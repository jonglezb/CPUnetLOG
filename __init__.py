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
        self.cpu = psutil.cpu_percent(interval=0, percpu=True)

        ## timing
        t2 = time.time()
        assert( t2-t < 0.001 )   ## XXX should be fast!!

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
        return "Timespan: " + str(self.timespan) + "; CPU: " + str(self.cpu)



## XXX for interactive debugging only
def test():
    print( Measurement() )


## init
init_measure = Measurement()

# measure
time.sleep(MEASUREMENT_INTERVAL)
m1 = Measurement()

## show
print( m1 )

