#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# processes.py - process-related statistics
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


"""Statistics for processes currently running and system load averages."""


import os
import rrdtool

from common import *

from templates.processes.index import index as OverviewPage
from templates.processes.load import load as LoadAveragePage
from templates.processes.forks import forks as ForkRatePage


#
# The file where we get our data from.
#
DATA_SOURCE = "/proc/loadavg"


class Processes(StatsComponent):
    """Statistics for Process Creation and System Load Averages."""
    def __init__(self):
        self.name = "processes"

        if not os.path.exists(DATA_SOURCE):
            fail(self.name, "cannot find \"%s\"." % DATA_SOURCE)
            raise StatsException(DATA_SOURCE + " does not exist")
        
        self.title = "Processes"
        self.description = "system load average and process spawning rates"

        self.data_dir = properties["data"] + "/" + self.name
        self.database = self.data_dir + "/processes.rrd"
        self.graphs_dir = properties["output"] + "/" + self.name

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.exists(self.graphs_dir):
            os.makedirs(self.graphs_dir)
            os.mkdir(self.graphs_dir + "/load")
            os.mkdir(self.graphs_dir + "/forks")

        if not os.path.exists(self.database):
            #
            # Remember: all "time" values are expressed in seconds.
            #
            refresh = properties["refresh"]
            heartbeat = refresh * 2
            rrdtool.create(self.database,
                           "--step", "%d" % refresh,
                           "DS:avg_1min:GAUGE:%d:0:U" % heartbeat,
                           "DS:avg_5min:GAUGE:%d:0:U" % heartbeat,
                           "DS:avg_15min:GAUGE:%d:0:U" % heartbeat,
                           "DS:proc:COUNTER:%d:0:U" % heartbeat,
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
        data = f.readline().split()
        f.close()

        rrdtool.update(self.database,
                       "--template", "avg_1min:avg_5min:avg_15min:proc",
                       "N:%s:%s:%s:%s" % (data[0], data[1], data[2], data[4]))

                       
    def make_graphs(self):
        """Generate the daily, weekly and monthly graphics."""
        height = str(properties["height"])
        width = str(properties["width"])
        refresh = properties["refresh"]
        background = properties["background"]
        border = properties["border"]

        for interval in ("1day", "1week", "1month", "1year"):
            rrdtool.graph("%s/load/graph-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still *unknown*
                          "--title", "running processes (load average)",
                          "--lazy",
                          "--base", "1000",
                          "--units-exponent", "0",  # disable automatic scaling of units
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "0.5",
                          "--imgformat", "PNG",
                          "--vertical-label", "processes",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:avg_5min=%s:avg_5min:AVERAGE" % self.database,
                          "AREA:avg_5min#32cd32:5 min average",
                          "GPRINT:avg_5min:LAST:\\: %6.2lf proc (now)",
                          "GPRINT:avg_5min:MAX:%6.2lf proc (max)",
                          "GPRINT:avg_5min:AVERAGE:%6.2lf proc (avg)")

            rrdtool.graph("%s/forks/graph-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still *unknown*
                          "--title", "process spawning (forks/sec)",
                          "--lazy",
                          "--base", "1000",
                          "--units-exponent", "0",  # disable automatic scaling of units
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "0.5",
                          "--imgformat", "PNG",
                          "--vertical-label", "forks/sec",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % background,
                          "--color", "SHADEB%s" % background,
                          "DEF:proc=%s:proc:AVERAGE" % self.database,
                          "AREA:proc#32cd32:processes",
                          "GPRINT:proc:LAST:\\: %6.2lf forks/sec (now)",
                          "GPRINT:proc:MAX:%6.2lf forks/sec (max)",
                          "GPRINT:proc:AVERAGE:%6.2lf forks/sec (avg)")

    def make_html(self):
        """Generate the HTML pages."""
        template = OverviewPage()
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        template = LoadAveragePage()
        template_fill(template, "running processes (load average)")
        template_write(template, self.graphs_dir + "/load/index.html")

        template = ForkRatePage()
        template_fill(template, "process spawning rates (forks/sec)")
        template_write(template, self.graphs_dir + "/forks/index.html")

        
# EOF - processes.py
