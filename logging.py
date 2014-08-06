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

## General
#general["Classes"] = ("Time", "CPU", "NIC", "RAM")
general["Classes"] = ("Time", "CPU", "NIC")
general["Type"] = None
general["Comment"] = ""
general["Begin"] = 0
general["End"] = 0
general["Duration"] = 0

top["General"] = general

## Classes

cpu = LoggingClass( name        = "CPU",
                    fields      = ("usr", "system", "softirq", "other"),
                    siblings    = [ "CPU" + str(i) for i in range(1,9) ],
                    description = "CPU utilization in percent" )
class_definitions[cpu.name] = cpu.values

nic = LoggingClass( name        = "NIC",
                    fields      = ("send", "receive"),
                    siblings    = [ "eth" + str(i) for i in range(1,3) ],
                    description = "Network traffic (Bits/s)" )
class_definitions[nic.name] = nic.values

nic = LoggingClass( name        = "Time",
                    fields      = ("begin", "end", "duration"),
                    siblings    = None,
                    description = "Begin, end, and duration of this measurement." )
class_definitions[nic.name] = nic.values

top["ClassDefinitions"] = class_definitions


## JSON

pretty_json = json.dumps(top, sort_keys=True, indent=4)

print( pretty_json )


## CSV header
csv_header = list()

for _class in general["Classes"]:
#for _class in ("CPU", "NIC", ):
    c = class_definitions[_class]

    if ( c["Siblings"] ):
        for sibling in c["Siblings"]:
            for field in c["Fields"]:
                csv_header.append( ".".join([sibling, field]) )
    else:
        for field in c["Fields"]:
            csv_header.append( field )


print( ", ".join(csv_header) )


