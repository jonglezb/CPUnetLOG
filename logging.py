# -*- coding:utf-8 -*-

import json
import time
import os

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

    def __init__(self, num_cpus, nics, comment, filename):
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
                            fields      = ("usr", "system", "softirq", "other", "idle"),
                            siblings    = [ "CPU" + str(i) for i in range(1,num_cpus) ],
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
    def _create_json_header(self, class_names, class_defs, type, comment):
        top_level = dict()
        general = dict()
        class_definitions = dict()

        ## General
        general["Classes"] = class_names
        general["Type"] = type
        general["Comment"] = comment
        #general["Begin"] = begin
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
        ## TODO format?
        out_vector.extend( [measurement.r1.timestamp, measurement.r2.timestamp, measurement.timespan] )


    def _log_cpus(self, measurement, out_vector):
        for cpu in measurement.cpu_times_percent:
            #cpu_util = 100-cpu.idle
            other = 100 - sum( (cpu.user, cpu.system, cpu.softirq, cpu.idle) )

            out_vector.extend( [cpu.user, cpu.system, cpu.softirq, other, cpu.idle] )


    def _log_nics(self, measurement, out_vector):
        for nic in self.nics:
            values = measurement.net_io[nic]

            out_vector.extend( [values.ratio["bytes_sent"] * 8,    # Bits/s
                              values.ratio["bytes_recv"] * 8] )  # Bits/s



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
    def __init__(self, num_cpus, nics, comment, path):
        self.num_cpus = num_cpus
        self.nics = nics
        self.comment = comment
        self.path = path

        if ( path and not os.path.exists(path) ):
            os.makedirs(path)

        self.measurement_logger_enabled = False


    def enable_measurement_logger(self):
        # Create filename from date.
        date = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
        filename = self.path + "/" + date + ".cnl"

        # Make sure the filename is unique.
        i = 0
        while ( os.path.exists(filename) ):
            filename = self.path + "/" + date + "-" + str(i) + ".cnl"

        # Create Logger.
        self.measurement_logger = MeasurementLogger(self.num_cpus, self.nics, self.comment, filename)

        self.measurement_logger_enabled = True


    def log(self, measurement):
        if ( self.measurement_logger_enabled ):
            self.measurement_logger.log(measurement)


    def close(self):
        if ( self.measurement_logger_enabled ):
            self.measurement_logger.close()

