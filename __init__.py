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



## XXX TESTING
def display_cpu(measurement):
    num = 1
    for cpu in measurement.cpu_times_percent:
        print( "CPU" + str(num) + " util: " + str(100-cpu.idle) + "% (" + str(cpu.user) + "% user, " + str(cpu.system) + "% system)")
        num += 1

## XXX TESTING
def desplay_network_traffic(measurement, nics = None):
    if not nics:
        nics = measurement.net_io.keys()

    for nic in nics:
        values = measurement.net_io[nic]

        print( "[" + nic + "] Sending (bytes/s): " + str(values.ratio["packets_sent"]) +
              ", Receiving (bytes/s): " + str(values.ratio["packets_recv"]) )


## XXX TESTING
def display(measurement):
    nics = ("eth0", "wlan0")

    display_cpu(measurement)
    desplay_network_traffic( measurement, nics )


## XXX TESTING
def displayX(measurement):
    nic = "eth0"

    for cpu in measurement.cpu_times_percent:
        print( ", ".join([str(x) + "%" for x in cpu]))
        print( str(100-cpu.idle) + "%, " + str(cpu.user) + "%. " + str(cpu.system) + "%")
    for nic in measurement.net_io.keys():
        print( "[" + nic + "] " + str(measurement.net_io[nic]) )

    print




## XXX TESTING
def test_loop():
    for i in range(10):
        display( measure() )
        time.sleep(0.5)
        print


## XXX TESTING
#display( measure() )
test_loop()

