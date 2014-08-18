#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from collections import namedtuple
import os
import netifaces
import operator

_ptime_cpu_perc_nt = None


### Copied from »psutil« source code and adapted to calculate percentage on two input values rather than "live"
#     see: psutil/__init__.py:1282  (Version: 1.2.1-1ubuntu2)
def calculate_cpu_times_percent(cpu_times_older, cpu_times_younger, percpu=False):
    """Same as cpu_percent() but provides utilization percentages
    for each specific CPU time as is returned by cpu_times().
    For instance, on Linux we'll get:

      >>> cpu_times_percent()
      cpupercent(user=4.8, nice=0.0, system=4.8, idle=90.5, iowait=0.0,
                 irq=0.0, softirq=0.0, steal=0.0, guest=0.0, guest_nice=0.0)
      >>>

    interval and percpu arguments have the same meaning as in
    cpu_percent().
    """
    #global _last_cpu_times_2
    #global _last_per_cpu_times_2
#    blocking = interval is not None and interval > 0.0
    WINDOWS = os.name == 'nt'

    def calculate(t1, t2):
        global _ptime_cpu_perc_nt
        nums = []
        all_delta = sum(t2) - sum(t1)
        for field in t1._fields:
            field_delta = getattr(t2, field) - getattr(t1, field)
            try:
                field_perc = (100 * field_delta) / all_delta
            except ZeroDivisionError:
                field_perc = 0.0
            field_perc = round(field_perc, 1)
            if WINDOWS:
                # XXX
                # Work around:
                # https://code.google.com/p/psutil/issues/detail?id=392
                # CPU times are always supposed to increase over time
                # or at least remain the same and that's because time
                # cannot go backwards.
                # Surprisingly sometimes this might not be the case on
                # Windows where 'system' CPU time can be smaller
                # compared to the previous call, resulting in corrupted
                # percentages (< 0 or > 100).
                # I really don't know what to do about that except
                # forcing the value to 0 or 100.
                if field_perc > 100.0:
                    field_perc = 100.0
                elif field_perc < 0.0:
                    field_perc = 0.0
            nums.append(field_perc)
        if _ptime_cpu_perc_nt is None:
            _ptime_cpu_perc_nt = namedtuple('cpupercent', ' '.join(t1._fields))
        return _ptime_cpu_perc_nt(*nums)

    # system-wide usage
    if not percpu:
        #if blocking:
            #t1 = cpu_times()
            #time.sleep(interval)
        #else:
            #t1 = _last_cpu_times_2
        #_last_cpu_times_2 = cpu_times()
        #return calculate(t1, _last_cpu_times_2)
        return calculate(cpu_times_older, cpu_times_younger)
    # per-cpu usage
    else:
        ret = []
        #if blocking:
            #tot1 = cpu_times(percpu=True)
            #time.sleep(interval)
        #else:
            #tot1 = _last_per_cpu_times_2
        #_last_per_cpu_times_2 = cpu_times(percpu=True)
        for t1, t2 in zip(cpu_times_older, cpu_times_younger):
            ret.append(calculate(t1, t2))
        return ret



def get_nics():
    return netifaces.interfaces()

def get_nic_speeds():
    ret = dict()

    for nic in get_nics():
        try:
            with open("/sys/class/net/" + nic + "/speed", "r") as f:
                speed = int( f.read().strip() ) * 1000 * 1000

            ret[nic] = speed
        except OSError:
            speed = 0

    return ret


def split_proprtionally(text, weights, size=0, fill=" "):
    """
    Split a string proportional to a given weight-distribution.

    If a |size| is specified, that string is filled with |fill| at the end to match that length.
    (NOTE: len(fill) must be 1)
    """

    if ( size > 0 ):
        ## Fill text with spaces.
        if ( len(text) < size ):
            text += fill * (size-len(text))
        ## Truncate text if it's too long.
        elif ( len(text) > size ):
            text = text[size]
    else:
        size = len(text)

    # sum of all weights
    total_weights = float( sum(weights) )

    ## Calculate an int for each weight so that they sum appropriately to |size|.
    float_lengths = [ (w / total_weights)*size for w in weights ]
    weighted_lengths = [ int(round( f )) for f in float_lengths ]

    ## Compensate rounding-related inconsistencies.
        # XXX I hope this actually does what's supposed to do...
        # (Increase/decrease the fields with the biggest rounding differences in order to fit the size)
    diff = size - sum(weighted_lengths)
    while( diff != 0 ):
        sign = -1 if diff < 0 else 1

        ## Calculate index where the rounding produced the biggest difference.
        #    (On equality, the latter one wins.)
        max_diff = 0
        index_of_max_diff = None
        for i in range( len(weighted_lengths) ):
            cur_diff = ( float_lengths[i] - weighted_lengths[i] ) * sign

            if ( cur_diff >= max_diff ):
                max_diff = cur_diff
                index_of_max_diff = i

        ## Increase the just found index by 1.
        weighted_lengths[i] += sign
        diff -= sign

    assert( sum(weighted_lengths) == size )



    ## * split *
    ret = list()
    last_pos = 0
    for pos in weighted_lengths:
        ret.append( text[last_pos:last_pos + pos] )
        last_pos += pos

    return ret


def get_sysinfo():
    #uname = os.uname()
    #input_fields = ("sysname", "nodename", "release", "version", "machine")

    output_fields = ("sysname", "hostname", "kernel", "version", "machine")

    ret = dict()
    for out_field, value in zip(output_fields, os.uname()):
        ret[out_field] = value

    return ret


def sort_named_tuple(data):
    return sorted( data._asdict().items() , key=operator.itemgetter(1), reverse=True)
