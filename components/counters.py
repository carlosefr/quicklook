#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# counters.py - network interface statistics
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


"""Statistics for all network interfaces present in the system (except the "loopback").
   Historical data for "bytes/sec" and "packets/sec" rates, both incoming and outgoing."""


import os
import re
import rrdtool

from components.common import *

from templates.counters.index import index as OverviewPage
from templates.counters.detailed import detailed as DetailsPage


#
# The file where we get our data from.
#
# This file is composed of two lines of headers followed by one
# or more lines, each referring to a network interface, including
# the "loopback". These lines have the following format (excluding
# the quotation marks and backslashes):
#
# "  interface_name:rx_bytes rx_packets rx_errs rx_drop rx_fifo \
#    rx_frame rx_compressed rx_multicast tx_bytes tx_packets tx_errs \
#    tx_drop tx_fifo tx_frame tx_compressed tx_multicast"
#
DATA_SOURCE = "/proc/net/dev"


class NetworkCounters(StatsComponent):
    """Network Interface Statistics."""
    def __init__(self):
        self.interfaces = {}

        self.name = "counters"

        if not os.path.exists(DATA_SOURCE):
            fail(self.name, "cannot find \"%s\"." % DATA_SOURCE)
            raise StatsException(DATA_SOURCE + " does not exist")
        
        self.title = "Network Interfaces"
        self.description = "network traffic rates"

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
            
    def update(self):
        """Read the system counters and update the historical
           data for all network interfaces currently \"up\"."""
        f = open(DATA_SOURCE, "r")

        # Skip both header lines.
        f.readline()
        f.readline()

        regexp = re.compile("\s*(.+):(.+)")

        for line in f:
            match = regexp.match(line)
            interface_name, values = match.groups()

            # Ignore the loopback interface.
            if interface_name == "lo":
                continue

            if interface_name in self.interfaces:
                interface = self.interfaces[interface_name]
            else:
                interface = NetworkInterface(interface_name, self.data_dir, self.graphs_dir)
                self.interfaces[interface_name] = interface

            data = values.split()
            interface.update(int(data[0]),  # tx_packets
                             int(data[8]),  # tx_bytes
                             int(data[1]),  # rx_packets
                             int(data[9]))  # rx_packets

        f.close()

    def make_graphs(self):
        """Generate the daily, weekly and monthly graphics for all network interfaces."""
        for interface in self.interfaces.values():
            interface.make_graphs()

    def make_html(self):
        """Generate the HTML pages for all network interfaces."""
        interfaces = self.interfaces.keys()
        interfaces.sort()
        
        template = OverviewPage()
        template.interfaces = interfaces
        
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        for interface in self.interfaces.values():
            interface.make_html()
        
            
class NetworkInterface(object):
    """Stores the historical data for a single network interface."""
    def __init__(self, name, data_dir, graphs_dir):
        self.name = name
        self.graphs_dir = graphs_dir + "/" + self.name
        self.database = data_dir + "/" + self.name + ".rrd"
        
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
                           "DS:rx_bytes:COUNTER:%d:0:U" % heartbeat,
                           "DS:tx_bytes:COUNTER:%d:0:U" % heartbeat,
                           "DS:rx_packets:COUNTER:%d:0:U" % heartbeat,
                           "DS:tx_packets:COUNTER:%d:0:U" % heartbeat,
                           "RRA:AVERAGE:0.5:1:%d" % (86400 / refresh),    # 1 day of 'refresh' averages
                           "RRA:AVERAGE:0.5:%d:672" % (900 / refresh),    # 7 days of 1/4 hour averages
                           "RRA:AVERAGE:0.5:%d:744" % (3600 / refresh),   # 31 days of 1 hour averages
                           "RRA:AVERAGE:0.5:%d:730" % (43200 / refresh))  # 365 days of 1/2 day averages

    def __str__(self):
        return self.name

    def update(self, rx_bytes, tx_bytes, rx_packets, tx_packets):
        """Update the historical data."""
        rrdtool.update(self.database,
                       "--template", "rx_bytes:tx_bytes:rx_packets:tx_packets",
                       "N:%d:%d:%d:%d" % (rx_bytes, tx_bytes, rx_packets, tx_packets))

    def make_graphs(self):
        """Generate daily, weekly, monthly and yearly byte and packet rates' graphics."""
        height = str(properties["height"])
        width = str(properties["width"])
        refresh = properties["refresh"]
        background = properties["background"]
        border = properties["border"]
        
        for interval in ("1day", "1week", "1month", "1year"):
            # graph bytes        
            rrdtool.graph("%s/graph-bytes-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still unknown
                          "--title", "%s - bytes/sec" % self.name,
                          "--lazy",
                          "--base", "1024",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "0.5",
                          "--imgformat", "PNG",
                          "--vertical-label", "bytes/sec",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:rx=%s:rx_bytes:AVERAGE" % self.database,
                          "DEF:tx=%s:tx_bytes:AVERAGE" % self.database,
                          "CDEF:rx_kb=rx,1024,/",
                          "CDEF:tx_kb=tx,1024,/",
                          "AREA:rx#a0df05:Incoming",
                          "GPRINT:rx_kb:LAST:\\: %8.1lf KBps (now)",
                          "GPRINT:rx_kb:MAX:%8.1lf KBps (max)",
                          "GPRINT:rx_kb:AVERAGE:%8.1lf KBps (avg)\\n",
                          "LINE1:tx#808080:Outgoing",
                          "GPRINT:tx_kb:LAST:\\: %8.1lf KBps (now)",
                          "GPRINT:tx_kb:MAX:%8.1lf KBps (max)",
                          "GPRINT:tx_kb:AVERAGE:%8.1lf KBps (avg)")

            # graph packets
            rrdtool.graph("%s/graph-packets-%s.png" % (self.graphs_dir, interval), 
                          "--start", "-%s" % interval,
                          "--end", "-%d" % refresh,  # because the last data point is still unknown
                          "--title", "%s - packets/sec" % self.name,
                          "--lazy",
                          "--base", "1000",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "0.5",
                          "--imgformat", "PNG",
                          "--vertical-label", "packets/sec",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % background,
                          "--color", "SHADEB%s" % background,
                          "DEF:rx=%s:rx_packets:AVERAGE" % self.database,
                          "DEF:tx=%s:tx_packets:AVERAGE" % self.database,
                          "AREA:rx#a0df05:Incoming",
                          "GPRINT:rx:LAST:\\: %7.0lf packets/sec (now)",
                          "GPRINT:rx:MAX:%7.0lf packets/sec (max)",
                          "GPRINT:rx:AVERAGE:%7.0lf packets/sec (avg)\\n",
                          "LINE1:tx#808080:Outgoing",
                          "GPRINT:tx:LAST:\\: %7.0lf packets/sec (now)",
                          "GPRINT:tx:MAX:%7.0lf packets/sec (max)",
                          "GPRINT:tx:AVERAGE:%7.0lf packets/sec (avg)")

    def make_html(self):
        """Generate the bytes and packets HTML pages."""
        for kind in ("bytes", "packets"):
            template = DetailsPage()
            template.kind = kind
            template_fill(template, "traffic detail for " + self.name + " (" + kind + "/sec)")
            template_write(template, self.graphs_dir + "/" + kind + ".html")

        
# EOF - counters.py
