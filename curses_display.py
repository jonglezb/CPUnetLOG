# -*- coding:utf-8 -*-

'''
Curses display for »cpunetlog«.

This code is inspired and partially copied from »bwtop« written by
"Mahmoud Adel <mahmoud.adel2@gmail.com>" and distributed under the MIT license.
'''

import curses
import time

## XXX disable colors
disablecolorskipped = True

stdscr = None

## some "constants"/preferences
nics = None
divisor = 1000
rounding_digits = 2
unit = "KBytes"



def _format_net_speed(speed):
    return str( round(speed / divisor, rounding_digits) )



def init():
    global stdscr

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

    pressedkey = stdscr.getch()
    if pressedkey == ord('q'):
        return False

    stdscr.clear()
    stdscr.border(0)
    timenow = time.strftime("%H:%M:%S")
    stdscr.addstr(1, 1, 'CPUnetLOG          Time: {0}       Interval: {1}s'.format(timenow, round(measurement.timespan, 1)), curses.A_BOLD)
    stdscr.refresh()

    # display all nics (if not set otherwise)
    if nics:
        active_nics = nics
    else:
        active_nics = measurement.net_io.keys()

    y=3
    sum_sending = 0
    sum_receiving = 0

    ## display the values
    for nic in active_nics:
        values = measurement.net_io[nic]

        sending = _format_net_speed( values.ratio["bytes_sent"] )
        receiving = _format_net_speed( values.ratio["bytes_recv"] )
        sum_sending += values.ratio["bytes_sent"]
        sum_receiving += values.ratio["bytes_recv"]

        stdscr.addstr(y, 1, '{0}'.format(nic), curses.color_pair(1))
        stdscr.addstr(y, 20, 'Sent:', curses.color_pair(2))
        stdscr.addstr(y, 26, '{0} {1}/s'.format(sending, unit), curses.color_pair(3))
        stdscr.addstr(y, 50, 'Received:', curses.color_pair(2))
        stdscr.addstr(y, 60, '{0} {1}/s'.format(receiving,unit), curses.color_pair(3))

        y += 1

    ## Total
    y+=1
    stdscr.addstr(y, 1, 'Total:', curses.color_pair(4))
    stdscr.addstr(y, 20, 'Sent:', curses.color_pair(2))
    stdscr.addstr(y, 26, '{0} {1}/s'.format(_format_net_speed(sum_sending), unit), curses.color_pair(3) | curses.A_STANDOUT)
    stdscr.addstr(y, 50, 'Received:', curses.color_pair(2))
    stdscr.addstr(y, 60, '{0} {1}/s'.format(_format_net_speed(sum_receiving),unit), curses.color_pair(3) | curses.A_STANDOUT)

    stdscr.refresh()

    return True


def close():
    global stdscr

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.curs_set(True)
    curses.endwin()
