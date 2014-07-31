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

## TODO ideas..
#   - total (GB transferred)
#   - other (CPU usage)

## TODO idea: smoothing..?


def _format_net_speed(speed):
    return str( round(speed / divisor, rounding_digits) )


def _display_cpu_bar(y, x, cpu):
    # Constants
    CPU_BAR_COLORS = ( curses.color_pair(3) | curses.A_REVERSE,    # user
                       curses.color_pair(4) | curses.A_REVERSE,    # system
                       curses.color_pair(5) | curses.A_REVERSE,    # other
                       curses.color_pair(3) )                      # idle

    # Calculate proportions
    cpu_util = 100-cpu.idle
    other = 100 - sum( (cpu.user, cpu.system, cpu.idle) )
    proportions = [cpu.user, cpu.system, other, cpu.idle]

    # Prepare text.
    text = '{0:.2%}'.format((cpu_util)/100.0)
    split_text = helpers.split_proprtionally(text, proportions, 20)

    # Write text on screen (curses).
    stdscr.move(y,x)
    for s, options in zip(split_text, CPU_BAR_COLORS):
        stdscr.addstr(s, options)




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
        curses.init_pair(1, curses.COLOR_MAGENTA, -1)         # "CPUX", "ethX"
        curses.init_pair(2, curses.COLOR_BLUE, -1)            # "util", "sent", "received", ...
        curses.init_pair(3, curses.COLOR_GREEN, -1)           # <values>
        curses.init_pair(4, curses.COLOR_YELLOW, -1)          # "Total", (<cpu-system> ?)
        curses.init_pair(5, curses.COLOR_CYAN, -1)            # <cpu-system> / <cpu-other>
        curses.init_pair(6, curses.COLOR_WHITE, -1)           # <cpu-system> / <cpu-other>

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
        # static labels
        stdscr.addstr(y, 1, 'CPU{0}'.format( num ), curses.color_pair(1))
        stdscr.addstr(y, 20, 'util:', curses.color_pair(2))
        stdscr.addstr(y, 50, 'user:', curses.color_pair(2))
        stdscr.addstr(y, 66, 'system:', curses.color_pair(2))

        # CPU bar
        _display_cpu_bar( y, 26, cpu )

        # user/system
        stdscr.addstr(y, 56, '{0:.2%}'.format( cpu.user/100.0 ), curses.color_pair(3))
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
        stdscr.addstr(y, 20, 'Sent: |', curses.color_pair(2))
        stdscr.addstr(y, 50, 'Received: |', curses.color_pair(2))
        stdscr.addstr(y, 47, "|", curses.color_pair(2))
        stdscr.addstr(y, 81, "|", curses.color_pair(2))

        ## XXX prototypical "inline"-coloring
        _snd_str = '{0} {1}/s'.format(sending, unit, send_ratio)
        _snd_str += " " * (20-len(_snd_str))
        _load_len = int(send_ratio * 20)
        stdscr.addstr(y, 27, _snd_str[0:_load_len], curses.color_pair(3)|curses.A_REVERSE)
        stdscr.addstr(y, 27+_load_len, _snd_str[_load_len:], curses.color_pair(3))

        _recv_str = '{0} {1}/s'.format(receiving, unit, send_ratio)
        _recv_str += " " * (20-len(_recv_str))
        _load_len = int(receive_ratio * 20)
        stdscr.addstr(y, 61, _recv_str[0:_load_len], curses.color_pair(3)|curses.A_REVERSE)
        stdscr.addstr(y, 61+_load_len, _recv_str[_load_len:], curses.color_pair(3))

        ## XXX TESTING
        #y += 1
        #stdscr.addstr(y, 25, "|" + " "*20 + "|", curses.color_pair(2))
        #stdscr.addstr(y, 26, " " * int(send_ratio * 20), curses.color_pair(3)|curses.A_REVERSE)
        #stdscr.addstr(y, 59, "|" + " "*20 + "|", curses.color_pair(2))
        #stdscr.addstr(y, 60, " " * int(receive_ratio * 20), curses.color_pair(3)|curses.A_REVERSE)

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
