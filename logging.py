# -*- coding:utf-8 -*-

# Copyright (c) 2014,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# This code is provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock


import json
import time
import os
import psutil

## experimental "tcp_probe"
#import subprocess
#import signal

from history_store import HistoryStore


class LoggingClass:
    def __init__(self, name, fields, siblings, description):
        self.name = name

        self.values = dict()
        self.values["Fields"] = fields
        self.values["Siblings"] = siblings
        self.values["Description"] = description



class MeasurementLogger:
    """
    Logs the given »Measurements« (derived from two »Readings«) into a JSON-header CSV-body file.
    """

    ## Initialization ##

    def __init__(self, num_cpus, nics, begin, system_info, environment, comment, filename):
        ## Attributes
        self.num_cpus = num_cpus
        self.nics = nics
        self.filename = filename

        ## Constants / Characteristics
        self.class_names = ("Time", "CPU", "NIC")
        self.type_string = "CPUnetLOG:MeasurementLog"

        ## Run "outsourced" init functions.
        self.class_defs = self._init_class_definitions(num_cpus, nics)

        self.json_header = self._create_json_header(self.class_names,
                                                    self.class_defs.values(),
                                                    self.type_string,
                                                    begin,
                                                    system_info,
                                                    environment,
                                                    comment)

        self.csv_header = self._create_csv_header(self.json_header)


        ## Register special logging functions.
        self.log_functions = dict()
        self.log_functions["Time"] = self._log_time
        self.log_functions["CPU"] = self._log_cpus
        self.log_functions["NIC"] = self._log_nics


        ## Initialize file writer.
        self.writer = CNLFileWriter(filename)

        # Write header.
        self.writer.write_header(self.json_header)
        self.writer.write_vector(self.csv_header)



    def _init_class_definitions(self, num_cpus, nics):
        class_defs = dict()

        # set up "CPU" class
        cpu = LoggingClass( name        = "CPU",
                            fields      = ("util", "idle", "usr", "system", "irq", "softirq", "other"),
                            siblings    = [ "CPU" + str(i) for i in range(0,num_cpus) ],
                            description = "CPU utilization in percent" )
        class_defs["CPU"] = cpu

        # set up "NIC" class
        nic = LoggingClass( name        = "NIC",
                            fields      = ("send", "receive"),
                            siblings    = nics,
                            description = "Network traffic (Bits/s)" )
        class_defs["NIC"] = nic

        # set up "Time" class
        time = LoggingClass( name        = "Time",
                            fields      = ("begin", "end", "duration"),
                            siblings    = None,
                            description = "Begin, end, and duration (in seconds) of this measurement." )
        class_defs["Time"] = time

        return class_defs


    ## TODO Move this outside the class?
    def _create_json_header(self, class_names, class_defs, type, begin, system_info, environment, comment):
        top_level = dict()
        general = dict()
        class_definitions = dict()

        ## General
        general["Classes"] = class_names
        general["Type"] = type
        general["Comment"] = comment
        general["Date"] = begin
        general["SystemInfo"] = system_info
        general["Environment"] = environment
        #general["End"] = 0        ## TODO ... can't be written at the beginning of the file!!
        #general["Duration"] = 0   ## TODO
        top_level["General"] = general

        ## Class definitions
        for c in class_defs:
            class_definitions[c.name] = c.values
        top_level["ClassDefinitions"] = class_definitions

        pretty_json = json.dumps(top_level, sort_keys=True, indent=4)

        return top_level


    ## TODO Move this outside the class?
    def _create_csv_header(self, json_header):
        csv_header = list()

        general = json_header["General"]
        class_definitions = json_header["ClassDefinitions"]

        for _class_name in general["Classes"]:
            _class = class_definitions[_class_name]

            if ( _class["Siblings"] ):
                for sibling in _class["Siblings"]:
                    for field in _class["Fields"]:
                        csv_header.append( ".".join([sibling, field]) )
            else:
                for field in _class["Fields"]:
                    csv_header.append( field )

        return csv_header




    ## Logging functions ##

    def _log_time(self, measurement, out_vector):
        out_vector.extend( [measurement.r1.timestamp, measurement.r2.timestamp, measurement.timespan] )


    def _log_cpus(self, measurement, out_vector):
        for cpu in measurement.cpu_times_percent:
            cpu_util = 100-cpu.idle
            other = 100 - sum( (cpu.user, cpu.system, cpu.irq, cpu.softirq, cpu.idle) )

            out_vector.extend( [cpu_util, cpu.idle, cpu.user, cpu.system, cpu.irq, cpu.softirq, other] )


    def _log_nics(self, measurement, out_vector):
        for nic in self.nics:
            try:
                values = measurement.net_io[nic]

                out_vector.extend( [values.ratio["bytes_sent"] * 8,    # Bits/s
                                values.ratio["bytes_recv"] * 8] )  # Bits/s
            except KeyError:
                ## TODO: is 0 a good value to log, in this case?
                out_vector.extend( (0, 0) )


    def log(self, measurement):
        out_vector = list()

        ## Call the specific log-function for each class (in the proper order).
        for c in self.class_names:
            self.log_functions[c](measurement, out_vector)

        self.writer.write_vector( out_vector )



    ## Close ##

    def close(self):
        self.writer.close()




class CNLFileWriter:
    """
    This class produces files in the »CNL« format.

    Usage:
      - Constructor( filename )
      - write_header( »Dictionary that gets converted into JSON.« )
      - write_vector( »Vector specifying the CSV-header« )
      - Loop:
          - write_vector( »Vector holding one line of data.« )
      - close()
    """

    def __init__(self, filename):
        self.filename = filename

        self.file = None
        self.header_written = False

        self._open_file()


    def _write(self, line):
        self.file.write(line)

    def _writeln(self):
        self.file.write("\n")


    def _open_file(self):
        self.file = open(self.filename, "w")
        self._write("%% CPUnetLOGv1\n")

    def write_header(self, header_dict):
        pretty_json = json.dumps(header_dict, sort_keys=True, indent=4)

        self._write( "%% Begin_Header\n" )
        self._write( pretty_json )
        self._writeln()
        self._write( "%% End_Header\n" )
        self._writeln()
        self._write( "%% Begin_Body\n" )

        self.header_written = True


    #def write_line(self, line):
        #self._write( line + "\n" )

    def write_vector(self, out_vector):
        line = ", ".join( map(str, out_vector) ) + "\n"

        self._write( line )


    def close(self):
        if ( self.header_written ):
            self._write( "%% End_Body\n" )

        if ( self.file ):
            self._writeln()
            self.file.close()




class LoggingManager:
    def __init__(self, num_cpus, nics, system_info, environment, comment, path, autologging, watch_experiment):
        self.num_cpus = num_cpus
        self.nics = nics
        self.comment = comment
        self.auto_comment = None
        self.path = path
        self.system_info = system_info
        self.hostname = system_info["hostname"]
        self.environment = environment
        self.watch_experiment = watch_experiment

        # auto-logging
        self.INACTIVITY_THRESHOLD       = 30   # seconds
        self.HISTORY_SIZE               = 5    # samples
        self.auto_logging = autologging
        if ( autologging ):
            self.log_history = HistoryStore(self.HISTORY_SIZE)
            self.logging_active = False
            self.inactivity_count = 0


        # "mkdir" on path, if necessary.
        if ( path and not os.path.exists(path) ):
            os.makedirs(path)


        ## Logger.
        self.measurement_logger = None
        self.measurement_logger_enabled = False




    def _start_new_measurement_logger(self, measurement=None):
        assert( not self.measurement_logger )

        # find start time
        if ( measurement ):
            t = measurement.get_begin()
        else:
            t = time.time()

        # Create filename from start time.
        date = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(t))
        filename_prefix = self.path + "/" + date + "-" + self.hostname
        filename = filename_prefix + ".cnl"

        # Make sure the filename is unique.
        i = 0
        while ( os.path.exists(filename) ):
            filename = filename_prefix + "-" + str(i) + ".cnl"
            i += 1

        ## experimental "tcp_probe"
        #tcpprobe_filename = filename[:-4] + ".tcpprobe"


        print( "Logging to file: " + filename )


        # Auto-comment: Store the command line of the observed tool/experiment.
        if ( self.watch_experiment ):
            self.auto_comment = self._find_cmd_line_of(self.watch_experiment)

        ## Read environment file (if given).
        if ( self.environment ):
            with open(self.environment) as f:
                environment = json.load(f)
        else:
            environment = None


        # Create Logger.
        self.measurement_logger = MeasurementLogger(self.num_cpus, self.nics, [date,t],
                                                    self.system_info, environment,
                                                    self.auto_comment if self.auto_comment else self.comment,
                                                    filename)


        ## experimental "tcp_probe"
        ## test if tcp_probe file is readable
        #PATH_TO_TCP_PROBE = "/proc/net/tcpprobe"
        #self.use_tcpprobe = os.access(PATH_TO_TCP_PROBE, os.R_OK)
        #if ( self.use_tcpprobe ):
            ### start "cat /proc/net/tcpprobe > file" in parallel (and send quit signal, when logging is stopped)
            #self.tcpprobe = subprocess.Popen("cat " + PATH_TO_TCP_PROBE + " > " + tcpprobe_filename, shell=True, preexec_fn=os.setsid)




    def _stop_measurement_logger(self):
        print( "Logging stopped. File: " + self.measurement_logger.filename )
        self.measurement_logger.close()

        self.measurement_logger = None
        self.auto_comment = None

        ## experimental "tcp_probe"
        ## kill "cat /proc/net/tcpprobe > file"
        #if ( self.use_tcpprobe ):
            #os.killpg(self.tcpprobe.pid, signal.SIGTERM)


    def _is_activity_on_nics(self, measurement):
        for nic in self.nics:
            try:
                values = measurement.net_io[nic]

                if ( values.ratio["bytes_sent"] > 0 or values.ratio["bytes_recv"] > 0 ):
                    return True
            except KeyError:
                pass

        return False



    def _log(self, measurement):
        if ( self.measurement_logger ):
            self.measurement_logger.log(measurement)



    def _find_cmd_line_of(self, name):
        hits = list()

        for p in psutil.process_iter():
            if ( p.name == name ):
                hits.append( " ".join(p.cmdline) )

        if ( len(hits) > 0 ):
            return "; ".join(hits)
            #return hits  ## TODO return a list; maybe introduce field "comments"/"watched_experiments"?

        return None


    def _auto_logging_transition_to_active(self):
        self.logging_active = True
        self.inactivity_count = 0

        ## Create a new measurement logger (if enabled).
        if ( self.measurement_logger_enabled ):
            self._start_new_measurement_logger()

        ## Log the new measurement, but also some history.
        for m in self.log_history.flush():
            self._log(m)



    def _auto_logging_process_in_inactive_state(self, measurement):
        ## Store measurement.
        self.log_history.push(measurement)

        ## If activity detected, start logging.
        if ( self._is_activity_on_nics(measurement) ):
            self._auto_logging_transition_to_active()

    def _auto_logging_process_in_active_state(self, measurement):
        ## Log measurement.
        self._log(measurement)

        ## Branch: Inactive sample.
        if ( not self._is_activity_on_nics(measurement) ):
            self.inactivity_count += measurement.timespan

            ## Inactivity phase too long: Stop logging.
            if ( self.inactivity_count >= self.INACTIVITY_THRESHOLD ):
                if ( self.measurement_logger_enabled ):
                    self._stop_measurement_logger()

                self.logging_active = False

                ## Stop everything!!  (XXX)
                #return False

        ## Branch: Active sample.
        else:
            self.inactivity_count = 0

        return True


    def _auto_logging(self, measurement):
        ## BRANCH: Logging inactive,
        #    wait for activity on observed nics.
        if ( not self.logging_active ):
            self._auto_logging_process_in_inactive_state(measurement)

            return True

        ## BRANCH: Logging active,
        #    log until observed nics get inactive.
        else:
            return self._auto_logging_process_in_active_state(measurement)

        ## Should be never reached.
        assert( False )


    def enable_measurement_logger(self):
        self.measurement_logger_enabled = True

        if ( not self.auto_logging ):
            self._start_new_measurement_logger()



    def log(self, measurement):

        ## BRANCH: no auto-logging, just call _log() directly.
        if ( not self.auto_logging ):
            self._log(measurement)

            return True

        ## BRANCH: Auto-logging
        else:
            return self._auto_logging(measurement)



    def get_logging_state(self):
        if ( not self.measurement_logger_enabled ):
            return "Disabled"

        # BRANCH: no auto-logging
        if ( not self.auto_logging ):
            return "Enabled"

        # BRANCH: auto-logging
        else:
            if ( self.logging_active ):
                if ( self.inactivity_count > 2 ):
                    return "(Active)"
                else:
                    return "Active"
            else:
                return "Standby"


    def get_logging_comment(self):
        return self.auto_comment if self.auto_comment else self.comment



    def close(self):
        if ( self.measurement_logger ):
            self._stop_measurement_logger()

