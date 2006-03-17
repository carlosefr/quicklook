#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# disks.py - disk statistics
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


"""Statistics for all disk drives in the system."""


import os
import re
import rrdtool

from common import *

from templates.disks.index import index as OverviewPage
from templates.disks.detailed import detailed as DetailsPage


#
# The files where we can get our data from.
#
DATA_SOURCE = "/proc/diskstats"
DATA_SOURCE_OLD = "/proc/partitions"  # 2.4.x <= linux < 2.6.x

# Number of fields on a device entry.
DEV_FIELD_COUNT = 14
DEV_FIELD_COUNT_OLD = 15  # 2.4.x <= linux < 2.6.x


class DiskStats(StatsComponent):
    """Disk Statistics."""
    def __init__(self):
        self.disks = {}

        self.name = "disks"

        if os.path.exists(DATA_SOURCE):
            self.old_stats = False
        elif os.path.exists(DATA_SOURCE_OLD):
            self.old_stats = True
        else:
            fail(self.name, "cannot find \"%s\" or \"%s\"." % (DATA_SOURCE, DATA_SOURCE_OLD))
            raise StatsException(DATA_SOURCE + " does not exist, neither does " + DATA_SOURCE_OLD)
        
        self.title = "Disk Storage"
        self.description = "I/O operation statistics"

        self.data_dir = properties["data"] + "/" + self.name
        self.graphs_dir = properties["output"] + "/" + self.name

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        if not os.path.exists(self.graphs_dir):
            os.makedirs(self.graphs_dir)

    def info(self):
        """Return some information about the component,
           as a tuple: (name, title, description)"""
        return (self.name, self.title, self.description)

    def _register_disk(self, disk_name):
        if self.disks.has_key(disk_name):
            disk = self.disks[disk_name]
        else:
            disk = Disk(disk_name, self.data_dir, self.graphs_dir)
            self.disks[disk_name] = disk
            
        return disk
        
    def _update_old(self):
        """Collect statistics on 2.4.x kernels."""
        f = open(DATA_SOURCE_OLD, "r")

        # Exclude partitions (only disks matter to us).
        exclude = re.compile("(part|(s|h)d[a-z]+)\d+")

        f.next()  # skip the header
        f.next()  # skip the blank line
        
        for line in f:
            values = line.split()
            if len(values) != DEV_FIELD_COUNT_OLD:
                fail(self.name, "cannot parse \"%s\"." % DATA_SOURCE_OLD)
                raise StatsException(DATA_SOURCE_OLD + ": wrong format")
            
            disk_name = values[3]
            
            # Disk names may appear in an hierarchical format,
            # such as "ide/host0/bus0/target0/lun0/disc", so
            # we must strip the "/"'s.
            disk_name = disk_name.replace("/", ".")

            if not exclude.search(disk_name):
                sectors_reads = int(values[6])
                sectors_writes = int(values[10])

                disk = self._register_disk(disk_name)        
                disk.update(sectors_reads, sectors_writes)
        
        f.close()        

    def _update(self):
        """Collect statistics on 2.6.x (or newer) kernels."""
        f = open(DATA_SOURCE, "r")

        # Exclude ramdisks, floppies and loop devices.
        exclude = re.compile("(ram|fd|loop)\d+")

        for line in f:
            values = line.split()
            disk_name = values[2]
            
            if len(values) == DEV_FIELD_COUNT and not exclude.search(disk_name):
                sectors_reads = int(values[5])
                sectors_writes = int(values[9])

                disk = self._register_disk(disk_name)
                disk.update(sectors_reads, sectors_writes)
        
        f.close()
        
    def update(self):
        """Read the system counters and update the
           historical data for all disks."""
        if self.old_stats:
            return self._update_old()
        else:
            return self._update()
           
    def make_graphs(self):
        """Generate the daily, weekly and monthly graphics for all disks."""
        for disk in self.disks.values():
            disk.make_graphs()

    def make_html(self):
        """Generate the HTML pages for all disks."""
        disks = self.disks.keys()
        disks.sort()
        
        template = OverviewPage()
        template.disks = disks
        
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        for disk in self.disks.values():
            disk.make_html()
        
            
class Disk(object):
    """Stores the historical data for a single disk."""
    def __init__(self, name, data_dir, graphs_dir):
        self.name = name
        self.graphs_dir = graphs_dir + "/" + self.name
        self.database = data_dir + "/" + self.name + ".rrd"
        
        if not os.path.exists(self.graphs_dir):
            os.makedirs(self.graphs_dir)

        if not os.path.exists(self.database):
            refresh = properties["refresh"]
            heartbeat = refresh * 2
            rrdtool.create(self.database,
                           "--step", "%d" % refresh,
                           "DS:sector_reads:COUNTER:%d:0:U" % heartbeat,
                           "DS:sector_writes:COUNTER:%d:0:U" % heartbeat,
                           "RRA:AVERAGE:0.5:1:%d" % (86400 / refresh),    # 1 day of 'refresh' averages
                           "RRA:AVERAGE:0.5:%d:672" % (900 / refresh),    # 7 days of 1/4 hour averages
                           "RRA:AVERAGE:0.5:%d:744" % (3600 / refresh),   # 31 days of 1 hour averages
                           "RRA:AVERAGE:0.5:%d:730" % (43200 / refresh))  # 365 days of 1/2 day averages

    def __str__(self):
        return self.name

    def update(self, sector_reads, sector_writes):
        """Update the historical data."""
        rrdtool.update(self.database,
                       "--template", "sector_reads:sector_writes",
                       "N:%d:%d" % (sector_reads, sector_writes))

    def make_graphs(self):
        """Generate daily, weekly, monthly and yearly graphics."""
        height = str(properties["height"])
        width = str(properties["width"])
        refresh = properties["refresh"]
        background = properties["background"]
        border = properties["border"]
        
        for interval in ("1day", "1week", "1month", "1year"):
            rrdtool.graph("%s/graph-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still unknown
                          "--title", "%s - sectors read/written" % self.name,
                          "--lazy",
                          "--base", "1000",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "1.0",
                          "--imgformat", "PNG",
                          "--vertical-label", "operations/sec",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:reads=%s:sector_reads:AVERAGE" % self.database,
                          "DEF:writes=%s:sector_writes:AVERAGE" % self.database,
                          "AREA:reads#32cd32:Reads ",
                          "GPRINT:reads:LAST:\\: %9.1lf op/sec (now)",
                          "GPRINT:reads:MAX:%9.1lf op/sec (max)",
                          "GPRINT:reads:AVERAGE:%9.1lf op/sec (avg)\\n",
                          "LINE2:writes#4169e1:Writes",
                          "GPRINT:writes:LAST:\\: %9.1lf op/sec (now)",
                          "GPRINT:writes:MAX:%9.1lf op/sec (max)",
                          "GPRINT:writes:AVERAGE:%9.1lf op/sec (avg)")
                          
    def make_html(self):
        """Generate the HTML pages."""
        template = DetailsPage()
        template_fill(template, "I/O details for " + self.name)
        template_write(template, self.graphs_dir + "/index.html")

        
# EOF - disks.py
