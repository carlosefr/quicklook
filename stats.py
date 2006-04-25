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
                     "\n\n" % os.path.basename(sys.argv[0]))

    sys.stdout.write("--data=<data directory>\n\tThe place where" \
                     " the data files will be stored. It will be" \
                     " created if\n\tit doesn't exist.\n\n")
                     
    sys.stdout.write("--output=<output directory>\n\tThe graphs" \
                     " and the HTML pages will be generated into" \
                     " this directory.\n\tIt will be created if it" \
                     " doesn't exist.\n\n")

    sys.stdout.write("--refresh=<minutes> (optional)\n\tData should be collected" \
                     " at \"minutes\" intervals. For instance, if you\n\tset" \
                     " a cron job to run this program every 10 minutes," \
                     " you must specify\n\t\"--refresh=10\". Whatever value" \
                     " you choose the first time you run this\n\tprogram, you" \
                     " must stick with it unless you delete the data files"
                     " and\n\tstart over.\n"
                     "\tSo, if you don't have a strong reason to do otherwise," \
                     " just stick with\n\tthe default value of %d minutes (by" \
                     " omitting this option).\n\n" % (properties["refresh"] / 60))

    sys.stdout.write("--verbose (optional)\n\tThis program doesn't print any" \
                     " messages unless they are clearly errors.\n\tThis means that" \
                     " no error is printed if a particular component isn't\n\tloaded" \
                     " and that is something to be expected on some setups. As an\n\t" \
                     "example, if the (kernel) module \"ip_conntrack\" isn't loaded, no\n\t" \
                     "network connection statistics can be collected, but this is" \
                     " normal if\n\tthere is no active firewall on the machine.\n" \
                     "\tThis flag makes this program print these types of messages," \
                     " and it is\n\trecommended to use it at least once to see if" \
                     " everything is being\n\tloaded (or not).\n\n")
                     
    sys.stdout.write("* %s v%s\n\n" % (NAME, VERSION))


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
        elif option in ("-d", "--data"):
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
