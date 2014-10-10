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
import netifaces
import operator


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


def sort_named_tuple(data, skip=None):
    """
    Sort a named tuple by its values.

    With |skip| a value can be specified that is excluded from the result.
    """

    d = data._asdict()

    # NOTE: Possible improvement: Accept a list in skip?
    if ( skip ):
        del d[skip]

    return sorted( d.items() , key=operator.itemgetter(1), reverse=True)
