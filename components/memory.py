#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# memory.py - Memory usage statistics
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


"""Statistics for memory usage."""


import os
import rrdtool
import re

from common import *
from templates.memory.index import index as MemoryPage


#
# The file where we get our data from.
#
DATA_SOURCE = "/proc/meminfo"


class MemoryUsage(StatsComponent):
    """Memory Usage Statistics."""
    def __init__(self):
        # Total values for memory and swap, in KBytes.
        self.memory = 0
        self.swap = 0   

        self.name = "memory"

        if not os.path.exists(DATA_SOURCE):
            fail(self.name, "cannot find \"%s\"." % DATA_SOURCE)
            raise StatsException(DATA_SOURCE + " does not exist")
        
        self.title = "Memory"
        self.description = "memory and swap usage"

        self.data_dir = properties["data"] + "/" + self.name
        self.database = self.data_dir + "/memory.rrd"
        self.graphs_dir = properties["output"] + "/" + self.name

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.exists(self.graphs_dir):
            os.makedirs(self.graphs_dir)

        if not os.path.exists(self.database):
            #
            # Remember: all "time" values are expressed in seconds.
            #
            refresh = properties["refresh"]
            heartbeat = refresh * 2
            rrdtool.create(self.database,
                           "--step", "%d" % refresh,
                           "DS:memused:GAUGE:%d:0:U" % heartbeat,
                           "DS:buffers:GAUGE:%d:0:U" % heartbeat,
                           "DS:cached:GAUGE:%d:0:U" % heartbeat,
                           "DS:swapused:GAUGE:%d:0:U" % heartbeat,
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

        # Everything is in KBytes
        regexp = re.compile("MemTotal:\s+(\d+)" \
                            ".+\sMemFree:\s+(\d+)" \
                            ".+\sBuffers:\s+(\d+)" \
                            ".+\sCached:\s+(\d+)" \
                            ".+\sSwapTotal:\s+(\d+)" \
                            ".+\sSwapFree:\s+(\d+)")

        lines = [line.strip() for line in f]
        text = " ".join(lines)

        f.close()        

        match = regexp.search(text)
        if not match:
            raise StatsError("cannot parse " + DATA_SOURCE)

        memtotal, memfree, buffers, cached, swaptotal, swapfree = match.groups()
        
        memtotal, memfree, buffers, cached = int(memtotal), int(memfree), int(buffers), int(cached)
        swaptotal, swapfree = int(swaptotal), int(swapfree)
        
        memused = memtotal - (memfree + buffers + cached)
        swapused = swaptotal - swapfree

        self.memory = memtotal
        self.swap = swaptotal

        rrdtool.update(self.database,
                       "--template", "memused:buffers:cached:swapused",
                       "N:%d:%d:%d:%d" % (memused * 1024, buffers * 1024, cached * 1024, swapused * 1024))
                       
    def make_graphs(self):
        """Generate the daily, weekly and monthly graphics."""
        height = str(properties["height"])
        width = str(properties["width"])
        refresh = properties["refresh"]
        background = properties["background"]
        border = properties["border"]

        for interval in ("1day", "1week", "1month", "1year"):
            rrdtool.graph("%s/graph-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still *unknown*
                          "--title", "memory and swap usage (bytes)",
                          "--lazy",
                          "--base", "1024",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--imgformat", "PNG",
                          "--vertical-label", "bytes",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:memused=%s:memused:AVERAGE" % self.database,
                          "DEF:buffers=%s:buffers:AVERAGE" % self.database,
                          "DEF:cached=%s:cached:AVERAGE" % self.database,
                          "DEF:swapused=%s:swapused:AVERAGE" % self.database,
                          "CDEF:memused_mb=memused,1024,1024,*,/",
                          "CDEF:buffers_mb=buffers,1024,1024,*,/",
                          "CDEF:cached_mb=cached,1024,1024,*,/",
                          "CDEF:swapused_mb=swapused,1024,1024,*,/",
                          "AREA:memused#32cd32:Memory ",
                          "GPRINT:memused_mb:LAST:\\: %6.0lf MB (now)",
                          "GPRINT:memused_mb:MAX:%6.0lf MB (max)",
                          "GPRINT:memused_mb:AVERAGE:%6.0lf MB (avg)\\n",
                          "STACK:buffers#95e595:Buffers",
                          "GPRINT:buffers_mb:LAST:\\: %6.0lf MB (now)",
                          "GPRINT:buffers_mb:MAX:%6.0lf MB (max)",
                          "GPRINT:buffers_mb:AVERAGE:%6.0lf MB (avg)\\n",
                          "STACK:cached#d7f5d7:Cached ",
                          "GPRINT:cached_mb:LAST:\\: %6.0lf MB (now)",
                          "GPRINT:cached_mb:MAX:%6.0lf MB (max)",
                          "GPRINT:cached_mb:AVERAGE:%6.0lf MB (avg)",
                          "COMMENT:        Total Memory  :  %.0f MB\\n" % (float(self.memory) / 1024),
                          "LINE2:swapused#4169e1:Swap   ",
                          "GPRINT:swapused_mb:LAST:\\: %6.0lf MB (now)",
                          "GPRINT:swapused_mb:MAX:%6.0lf MB (max)",
                          "GPRINT:swapused_mb:AVERAGE:%6.0lf MB (avg)",
                          "COMMENT:        Total Swap    :  %.0f MB" % (float(self.swap) / 1024))

    def make_html(self):
        """Generate the HTML pages."""
        template = MemoryPage()
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        
# EOF - memory.py
