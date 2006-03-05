#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# cpu.py - CPU statistics
#
# Copyright (c) 2006, Carlos Rodrigues <cefrodrigues@mail.telepac.pt>
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


"""Statistics for CPU usage."""


import os
import rrdtool
import re

from components.common import *
from templates.cpu.index import index as CPUPage


#
# The file where we get our data from.
#
DATA_SOURCE = "/proc/stat"


class CPUUsage(StatsComponent):
    """CPU Usage Statistics."""
    def __init__(self):
        self.cpu_count = 0
        
        self.name = "cpu"

        if not os.path.exists(DATA_SOURCE):
            fail(self.name, "cannot find \"%s\"." % DATA_SOURCE)
            raise StatsException(DATA_SOURCE + " does not exist")
        
        self.title = "CPU"
        self.description = "CPU usage (overview)"

        self.data_dir = properties["data"] + "/" + self.name
        self.database = self.data_dir + "/cpu.rrd"
        self.graphs_dir = properties["output"] + "/" + self.name

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.exists(self.graphs_dir):
            os.makedirs(self.graphs_dir)

        if not os.path.exists(self.database):
            #
            # Remember: all "time" values are expressed in jiffies (1/100 seconds).
            #
            refresh = properties["refresh"]
            heartbeat = refresh * 2
            rrdtool.create(self.database,
                           "--step", "%d" % refresh,
                           "DS:user:COUNTER:%d:0:U" % heartbeat,
                           "DS:nice:COUNTER:%d:0:U" % heartbeat,
                           "DS:system:COUNTER:%d:0:U" % heartbeat,
                           "RRA:AVERAGE:0.5:1:%d" % (86400 / refresh),    # 1 day of 'refresh' averages
                           "RRA:AVERAGE:0.5:%d:672" % (900 / refresh),    # 7 days of 1/4 hour averages
                           "RRA:AVERAGE:0.5:%d:744" % (3600 / refresh),   # 31 days of 1 hour averages
                           "RRA:AVERAGE:0.5:%d:730" % (43200 / refresh))  # 365 days of 1/2 day averages

    def info(self):
        """Return some information about the component,
           as a tuple: (name, title, description)"""
        return (self.name, self.title, self.description)

    def update(self):
        """Update the historical data."""
        f = open(DATA_SOURCE, "r")

        regexp = re.compile("cpu\s+(\d+)\s+(\d+)\s+(\d+)")
        line = f.readline()
        match = regexp.match(line)
        if not match:
            raise StatsError("cannot parse " + DATA_SOURCE)

        # All these values represent an accumulated time since boot.
        # The unit is jiffies (1/100 seconds).
        user, nice, system = match.groups()
        user, nice, system = int(user), int(nice), int(system)

        regexp = re.compile("cpu\d*")
        self.cpu_count = 0
        for line in f:
            if regexp.match(line):
                self.cpu_count += 1
            
        f.close()

        rrdtool.update(self.database,
                       "--template", "user:nice:system",
                       "N:%d:%d:%d" % (user, nice, system))
        
    def make_graphs(self):
        """Generate the daily, weekly and monthly graphics."""
        height = str(properties["height"])
        width = str(properties["width"])
        refresh = properties["refresh"]
        background = properties["background"]
        border = properties["border"]

        # Since the values stored into the database are in 1/100th of a
        # second units, the resulting "rate" is already a percentage,
        # so no extra calculations are needed.
        for interval in ("1day", "1week", "1month", "1year"):
            rrdtool.graph("%s/graph-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still *unknown*
                          "--title", "CPU usage (%%) over %d processor(s)" % self.cpu_count,
                          "--lazy",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "100.0",
                          "--imgformat", "PNG",
                          "--vertical-label", "percentage",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:user=%s:user:AVERAGE" % self.database,
                          "DEF:system=%s:system:AVERAGE" % self.database,
                          "DEF:nice=%s:nice:AVERAGE" % self.database,
                          "AREA:user#32cd32:User  ",
                          "GPRINT:user:LAST:\\: %6.1lf%% (now)",
                          "GPRINT:user:MAX:%6.1lf%% (max)",
                          "GPRINT:user:AVERAGE:%6.1lf%% (avg)\\n",
                          "STACK:system#dc3c14:System",
                          "GPRINT:system:LAST:\\: %6.1lf%% (now)",
                          "GPRINT:system:MAX:%6.1lf%% (max)",
                          "GPRINT:system:AVERAGE:%6.1lf%% (avg)\\n",
                          "STACK:nice#ffe100:Nice  ",
                          "GPRINT:nice:LAST:\\: %6.1lf%% (now)",
                          "GPRINT:nice:MAX:%6.1lf%% (max)",
                          "GPRINT:nice:AVERAGE:%6.1lf%% (avg)")
                         
    def make_html(self):
        """Generate the HTML pages."""
        template = CPUPage()
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        
# EOF - cpu.py
