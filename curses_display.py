# -*- coding:utf-8 -*-

'''
Curses display for »cpunetlog«.

This code is inspired and partially copied from »bwtop« written by
"Mahmoud Adel <mahmoud.adel2@gmail.com>" and distributed under the MIT license.
'''

import curses
import time
import helpers

## XXX disable colors
disablecolorskipped = True

stdscr = None

## some "constants"/preferences
nics = None
nic_speeds = None
divisor = 1000000.0
rounding_digits = 2
unit = "MBits"



def _format_net_speed(speed):
    return str( round(speed / divisor, rounding_digits) )



def init():
    global stdscr
    global nic_speeds

    if not nic_speeds:
        nic_speeds = helpers.get_nic_speeds()

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    curses.curs_set(False)
    stdscr.nodelay(True)

    curses.start_color()
    curses.use_default_colors()
    if not disablecolorskipped:
        curses.init_pair(1, -1, -1)
        curses.init_pair(2, -1, -1)
        curses.init_pair(3, -1, -1)
        curses.init_pair(4, -1, -1)
    else:
        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        curses.init_pair(2, curses.COLOR_BLUE, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)

    ## Show some output to avoid upsetting the user
    stdscr.addstr(3, 3, "loading ...", curses.A_BOLD)
    stdscr.refresh()



def display(measurement):
    global stdscr

    ## Press 'q' to quit.
    pressedkey = stdscr.getch()
    if pressedkey == ord('q'):
        return False

    ## Header
    stdscr.clear()
    stdscr.border(0)
    timenow = time.strftime("%H:%M:%S")
    stdscr.addstr(1, 1, 'CPUnetLOG          Time: {0}                Interval: {1}s'.format(timenow, round(measurement.timespan, 1)), curses.A_BOLD)
    stdscr.refresh()

    y = 3

    ## CPU ##
    num=1
    for cpu in measurement.cpu_times_percent:
        stdscr.addstr(y, 1, 'CPU{0}'.format( num ), curses.color_pair(1))
        stdscr.addstr(y, 20, 'util:', curses.color_pair(2))
        stdscr.addstr(y, 26, '{0:.2%}'.format( (100-cpu.idle)/100.0 ), curses.color_pair(3))
        stdscr.addstr(y, 50, 'user:', curses.color_pair(2))
        stdscr.addstr(y, 56, '{0:.2%}'.format( cpu.user/100.0 ), curses.color_pair(3))
        stdscr.addstr(y, 66, 'system:', curses.color_pair(2))
        stdscr.addstr(y, 74, '{0:.2%}'.format( cpu.system/100.0 ), curses.color_pair(3))

        num += 1
        y += 1




    ## Network ##

    y += 1
    stdscr.hline(y, 1, "-", 85)
    y += 1

    # display all nics (if not set otherwise)
    if nics:
        active_nics = nics
    else:
        active_nics = measurement.net_io.keys()

    sum_sending = 0
    sum_receiving = 0

    ## display the values
    for nic in active_nics:
        values = measurement.net_io[nic]

        _send = values.ratio["bytes_sent"] * 8  # Bits/s
        _recv = values.ratio["bytes_recv"] * 8  # Bits/s
        sending = _format_net_speed( _send )
        send_ratio = _send/nic_speeds[nic]
        receiving = _format_net_speed( _recv )
        receive_ratio = _recv/nic_speeds[nic]

        sum_sending += _send
        sum_receiving += _recv

        stdscr.addstr(y, 1, '{0}'.format(nic), curses.color_pair(1))
        stdscr.addstr(y, 20, 'Sent:', curses.color_pair(2))
        stdscr.addstr(y, 26, '{0} {1}/s ({2:.2%})'.format(sending, unit, send_ratio), curses.color_pair(3))
        stdscr.addstr(y, 50, 'Received:', curses.color_pair(2))
        stdscr.addstr(y, 60, '{0} {1}/s ({2:.2%})'.format(receiving,unit, receive_ratio), curses.color_pair(3))

        ## XXX TESTING
        y += 1
        stdscr.addstr(y, 25, "|" + " "*20 + "|", curses.color_pair(2))
        stdscr.addstr(y, 26, " " * int(send_ratio * 20), curses.color_pair(3)|curses.A_REVERSE)
        stdscr.addstr(y, 59, "|" + " "*20 + "|", curses.color_pair(2))
        stdscr.addstr(y, 60, " " * int(receive_ratio * 20), curses.color_pair(3)|curses.A_REVERSE)

        y += 1

    ## Total
    y+=1
    stdscr.addstr(y, 1, 'Total:', curses.color_pair(4))
    stdscr.addstr(y, 20, 'Sent:', curses.color_pair(2))
    #stdscr.addstr(y, 26, '{0} {1}/s'.format(_format_net_speed(sum_sending), unit), curses.color_pair(3) | curses.A_STANDOUT)
    stdscr.addstr(y, 26, '{0} {1}/s'.format(_format_net_speed(sum_sending), unit), curses.color_pair(3))
    stdscr.addstr(y, 50, 'Received:', curses.color_pair(2))
    #stdscr.addstr(y, 60, '{0} {1}/s'.format(_format_net_speed(sum_receiving),unit), curses.color_pair(3) | curses.A_STANDOUT)
    stdscr.addstr(y, 60, '{0} {1}/s'.format(_format_net_speed(sum_receiving),unit), curses.color_pair(3))

    stdscr.refresh()

    return True


def close():
    global stdscr

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.curs_set(True)
    curses.endwin()
