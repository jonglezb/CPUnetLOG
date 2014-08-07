# -*- coding:utf-8 -*-

import json

class LoggingClass:
    def __init__(self, name, fields, siblings, description):
        self.name = name

        self.values = dict()
        self.values["Fields"] = fields
        self.values["Siblings"] = siblings
        self.values["Description"] = description



## Header definition

top = dict()
general = dict()
class_definitions = dict()

### General
##general["Classes"] = ("Time", "CPU", "NIC", "RAM")
#general["Classes"] = ("Time", "CPU", "NIC")
#general["Type"] = None
#general["Comment"] = ""
#general["Begin"] = 0
#general["End"] = 0
#general["Duration"] = 0

top["General"] = general

## Classes

#cpu = LoggingClass( name        = "CPU",
                    #fields      = ("usr", "system", "softirq", "other"),
                    #siblings    = [ "CPU" + str(i) for i in range(1,9) ],
                    #description = "CPU utilization in percent" )
#class_definitions[cpu.name] = cpu.values

#nic = LoggingClass( name        = "NIC",
                    #fields      = ("send", "receive"),
                    #siblings    = [ "eth" + str(i) for i in range(1,3) ],
                    #description = "Network traffic (Bits/s)" )
#class_definitions[nic.name] = nic.values

#time = LoggingClass( name        = "Time",
                    #fields      = ("begin", "end", "duration"),
                    #siblings    = None,
                    #description = "Begin, end, and duration of this measurement." )
#class_definitions[time.name] = time.values

#top["ClassDefinitions"] = class_definitions


#### JSON

##pretty_json = json.dumps(top, sort_keys=True, indent=4)

##print( pretty_json )


#### CSV header
##csv_header = list()

##for _class in general["Classes"]:
###for _class in ("CPU", "NIC", ):
    ##c = class_definitions[_class]

    ##if ( c["Siblings"] ):
        ##for sibling in c["Siblings"]:
            ##for field in c["Fields"]:
                ##csv_header.append( ".".join([sibling, field]) )
    ##else:
        ##for field in c["Fields"]:
            ##csv_header.append( field )


##print( ", ".join(csv_header) )




class MeasurementLogger:
    """
    Logs the given »Measurements« (derived from two »Readings«) into a JSON-header CSV-body file.
    """

    ## Initialization ##

    def __init__(self, begin, num_cpus, nics, comment, filename):
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

        ## XXX
        print( pretty_json )

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

        ## XXX
        print( ", ".join(csv_header) )

        return csv_header




    ## Logging functions ##

    def _log_time(self, measurement, log_line):
        ## TODO format?
        log_line.extend( [measurement.r1.timestamp, measurement.r2.timestamp, measurement.timespan] )


    def _log_cpus(self, measurement, log_line):
        for cpu in measurement.cpu_times_percent:
            #cpu_util = 100-cpu.idle
            other = 100 - sum( (cpu.user, cpu.system, cpu.softirq, cpu.idle) )

            log_line.extend( [cpu.user, cpu.system, cpu.softirq, other, cpu.idle] )


    def _log_nics(self, measurement, log_line):
        for nic in self.nics:
            values = measurement.net_io[nic]

            log_line.extend( [values.ratio["bytes_sent"] * 8,    # Bits/s
                              values.ratio["bytes_recv"] * 8] )  # Bits/s



    def log(self, measurement):
        log_line = list()

        ## Call the specific log-function for each class (in the proper order).
        for c in self.class_names:
            self.log_functions[c](measurement, log_line)

        ## XXX
        print( log_line )



    ## Close ##

    def close(self):
        ## TODO
        pass
