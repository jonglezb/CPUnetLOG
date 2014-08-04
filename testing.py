# -*- coding:utf-8 -*-

## XXX TESTING
def display_cpu(measurement):
    num = 1
    for cpu in measurement.cpu_times_percent:
        print( "CPU" + str(num) + " util: " + str(100-cpu.idle) + "% (" + str(cpu.user) + "% user, " + str(cpu.system) + "% system)")
        num += 1

## XXX TESTING
def desplay_network_traffic(measurement, nics = None):
    divisor = 1000
    rounding_digits = 2
    unit = "KBytes"

    if not nics:
        nics = measurement.net_io.keys()

    for nic in nics:
        values = measurement.net_io[nic]

        sending = str( round(values.ratio["bytes_sent"] / divisor, rounding_digits) )
        receiving = str( round(values.ratio["bytes_recv"] / divisor, rounding_digits) )

        print( "[" + nic + "] Sending (" + unit + "/s): " + sending +
              ", Receiving (" + unit + "/s): " + receiving )


## XXX TESTING
def display(measurement):
    #nics = ("eth0", "wlan0", "lo")
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
