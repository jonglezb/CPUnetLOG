# -*- coding:utf-8 -*-

### This code was originally copied from »psutil« source code and adapted
#   to calculate the percentage values on two input values rather than "live".
#     see: psutil/__init__.py:1282  (Version: 1.2.1-1ubuntu2)
#
#
# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of all psutils code in this file is governed by a BSD-style license that
# can also be found in the LICENSE.txt file.
#
#
# Copyright (c) 2014,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# The modifications are provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock

import os
from collections import namedtuple

_ptime_cpu_perc_nt = None

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

