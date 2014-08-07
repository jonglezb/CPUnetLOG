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
    def __init__(self, begin, num_cpus, nics, comment, filename):
        ## Attributes
        self.num_cpus = num_cpus
        self.nics = nics
        self.filename = filename

        self.classes = ("Time", "CPU", "NIC")
        self.log_functions = dict()
        self.log_functions["Time"] = self._log_time
        self.log_functions["CPU"] = self._log_cpus
        self.log_functions["NIC"] = self._log_nics


        ## General
        self.general = dict()
        self.general["Classes"] = self.classes
        self.general["Type"] = "CPUnetLOG:MeasurementLog"
        self.general["Comment"] = comment
        self.general["Begin"] = begin
        self.general["End"] = 0
        self.general["Duration"] = 0

        ## Classes

        # set up "CPU" class
        cpu = LoggingClass( name        = "CPU",
                            fields      = ("usr", "system", "softirq", "other", "idle"),
                            siblings    = [ "CPU" + str(i) for i in range(1,num_cpus) ],
                            description = "CPU utilization in percent" )

        # set up "NIC" class
        nic = LoggingClass( name        = "NIC",
                            fields      = ("send", "receive"),
                            siblings    = nics,
                            description = "Network traffic (Bits/s)" )

        # set up "Time" class
        time = LoggingClass( name        = "Time",
                             fields      = ("begin", "end", "duration"),
                             siblings    = None,
                             description = "Begin, end, and duration (in seconds) of this measurement." )



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
        for c in self.classes:
            self.log_functions[c](measurement, log_line)

        ## XXX
        print( log_line )


    def close(self):
        pass
