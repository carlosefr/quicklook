#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# stats.py - system statistics
#
# Copyright (c) 2005-2006, Carlos Rodrigues <cefrodrigues@mail.telepac.pt>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License (version 2) as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#


import os
import sys

from getopt import getopt, GetoptError

from components.common import *
from components.welcome import Welcome
from components.processes import Processes
from components.counters import NetworkCounters
from components.connections import NetworkConnections
from components.memory import MemoryUsage
from components.cpu import CPUUsage
from components.disks import DiskStats


def print_usage():
    sys.stdout.write("USAGE: %s" \
                     " --data=<data directory>" \
                     " --output=<output directory>" \
                     " [--refresh=<minutes>]" \
                     " [--verbose]" \
                     "\n" % os.path.basename(sys.argv[0]))


def process_cmdline():
    try:
        options, remaining = getopt(sys.argv[1:], "vd:o:r:", ["verbose", "data=", "output=", "refresh="])
    except GetoptError, exception:
        raise StatsError(str(exception))

    # These options are mandatory.
    data = output = False

    for option, value in options:
        if option in ("-v", "--verbose"):
            properties["verbose"] = True
        if option in ("-d", "--data"):
            properties["data"] = os.path.normpath(value)
            data = True
        elif option in ("-o", "--output"):
            properties["output"] = os.path.normpath(value)
            output = True
        elif option in ("-r", "--refresh"):
            try:
                properties["refresh"] = int(value) * 60
            except ValueError, e:
                raise StatsError("refresh must be a numeric value")
                
    if not data or not output:
        raise StatsError("not enough parameters")

        
def load_components():
    classes = ["CPUUsage", "MemoryUsage", "Processes", "DiskStats", "NetworkCounters", "NetworkConnections"]
    components = []

    for name in classes:
        try:
            # Instantiate the class dinamically.
            components.append(globals()[name]())
        except StatsException, e:
            pass

    return components
  
    
if __name__ == "__main__":
    try:
        process_cmdline()
    except StatsError, e:
        sys.stderr.write("Error: " + str(e) + "\n")
        print_usage()
        sys.exit(1)
        
    components = load_components()
    if len(components) == 0:
        sys.stderr.write("Error: no components could be loaded.")
        sys.exit(1)

    welcome = Welcome(components)
    welcome.update()
    welcome.make_html()
    
    for component in components:
        component.update()
        component.make_graphs()
        component.make_html()


# EOF - stats.py
