#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# connections.py - network connections statistics
#
# Copyright (c) 2005-2007, Carlos Rodrigues <cefrodrigues@mail.telepac.pt>
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


"""Statistics for all network connections currently known by the netfilter subsystem."""


import os
import rrdtool

from components.common import *
from templates.connections.index import index as ConnectionsPage


#
# The file where we get our data from.
#
DATA_SOURCE = "/proc/net/ip_conntrack"


class NetworkConnections(StatsComponent):
    """Network Connections Statistics."""
    def __init__(self):
        self.name = "connections"

        if not os.path.exists(DATA_SOURCE):
            fail(self.name, "maybe the kernel module 'ip_conntrack' isn't loaded.")
            raise StatsException(DATA_SOURCE + " does not exist")
        
        self.title = "Network Connections"
        self.description = "tracked connections, by protocol"
        self.data_dir = properties["data"] + "/" + self.name
        self.database = self.data_dir + "/protocol.rrd"
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
                           "DS:proto_tcp:GAUGE:%d:0:U" % heartbeat,
                           "DS:proto_udp:GAUGE:%d:0:U" % heartbeat,
                           "DS:proto_other:GAUGE:%d:0:U" % heartbeat,
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

        proto_tcp = 0
        proto_udp = 0
        proto_other = 0

        for line in f:
            data = line.split()
            proto = data[0].lower()

            if proto == "tcp":
                proto_tcp += 1
            elif proto == "udp":
                proto_udp += 1
            else:
                proto_other += 1

        f.close()

        rrdtool.update(self.database,
                       "--template", "proto_tcp:proto_udp:proto_other",
                       "N:%d:%d:%d" % (proto_tcp, proto_udp, proto_other))

                       
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
                          "--title", "network connections (by protocol)",
                          "--lazy",
                          "--base", "1000",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "10.0",
                          "--imgformat", "PNG",
                          "--vertical-label", "connections",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:proto_tcp=%s:proto_tcp:AVERAGE" % self.database,
                          "DEF:proto_udp=%s:proto_udp:AVERAGE" % self.database,
                          "DEF:proto_other=%s:proto_other:AVERAGE" % self.database,
                          "AREA:proto_tcp#a0df05:TCP  ",
                          "GPRINT:proto_tcp:LAST:\\: %6.0lf conn (now)",
                          "GPRINT:proto_tcp:MAX:%6.0lf conn (max)",
                          "GPRINT:proto_tcp:AVERAGE:%6.0lf conn (avg)\\n",
                          "STACK:proto_udp#ffe100:UDP  ",
                          "GPRINT:proto_udp:LAST:\\: %6.0lf conn (now)",
                          "GPRINT:proto_udp:MAX:%6.0lf conn (max)",
                          "GPRINT:proto_udp:AVERAGE:%6.0lf conn (avg)\\n",
                          "STACK:proto_other#dc3c14:Other",
                          "GPRINT:proto_other:LAST:\\: %6.0lf conn (now)",
                          "GPRINT:proto_other:MAX:%6.0lf conn (max)",
                          "GPRINT:proto_other:AVERAGE:%6.0lf conn (avg)")

    def make_html(self):
        """Generate the HTML pages."""
        template = ConnectionsPage()
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        
# EOF - connections.py
