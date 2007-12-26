#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# ups.py - UPS statistics (Network UPS Tools)
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


"""Statistics for all UPSes connected to the system."""


import os
import re
import rrdtool
import socket
import commands

from components.common import *

from templates.ups.index import index as OverviewPage
from templates.ups.detailed import detailed as DetailsPage


UPSD_HOST = "localhost"
UPSD_PORT = 3493


class UPSStats(StatsComponent):
    """UPS Statistics."""
    def __init__(self):
        self.name = "ups"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((UPSD_HOST, UPSD_PORT))
        except:
            fail(self.name, "cannot connect to upsd on \"%s:%d\"." % (UPSD_HOST, UPSD_PORT))
            raise StatsException("cannot connect to upsd")
        
        self.sock = sock.makefile("r+", 0)
        
        self.sock.write("VER\n")
        if not self.sock.readline().startswith("Network UPS Tools upsd"):
            fail(self.name, "the service listening on \"%s:%d\" isn't upsd." % (UPSD_HOST, UPSD_PORT))
            raise StatsException("bad response from server")            

        self.upses = {}

        self.title = "UPS"
        self.description = "UPS statistics"

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

    def _register_ups(self, ups_name):
        if ups_name in self.upses:
            ups = self.upses[ups_name]
        else:
            ups = UPS(ups_name, self.data_dir, self.graphs_dir)
            self.upses[ups_name] = ups
            
        return ups
        
    def update(self):
        """Get the current status and update the
           historical data for all UPSes."""
        self.sock.write("LIST UPS\n")
        self.sock.readline()

        regexp = re.compile("UPS\s+(\S+)\s+\"(.+)\"")

        for line in self.sock:
            if line.startswith("END LIST"):
                break

            self._register_ups(regexp.match(line).group(1))

        regexp = re.compile("VAR\s+\S+\s+\S+\s+\"(\S+)\"")

        for ups in self.upses.values():
            self.sock.write("GET VAR %s input.voltage\n" % ups)
            match = regexp.match(self.sock.readline())
            v_in = float(match.group(1))
            
            self.sock.write("GET VAR %s output.voltage\n" % ups)
            match = regexp.match(self.sock.readline())
            v_out = float(match.group(1))
            
            ups.update(v_in, v_out)
           
    def make_graphs(self):
        """Generate the daily, weekly and monthly graphics for all UPSes."""
        for ups in self.upses.values():
            ups.make_graphs()

    def make_html(self):
        """Generate the HTML pages for all UPSes."""
        upses = self.upses.keys()
        upses.sort()
        
        template = OverviewPage()
        template.upses = upses
        
        template_fill(template, self.description)
        template_write(template, self.graphs_dir + "/index.html")

        for ups in self.upses.values():
            ups.make_html()
        
            
class UPS(object):
    """Stores the historical data for a single UPS."""
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
                           "DS:v_in:GAUGE:%d:0:U" % heartbeat,
                           "DS:v_out:GAUGE:%d:0:U" % heartbeat,
                           "RRA:AVERAGE:0.5:1:%d" % (86400 / refresh),    # 1 day of 'refresh' averages
                           "RRA:AVERAGE:0.5:%d:672" % (900 / refresh),    # 7 days of 1/4 hour averages
                           "RRA:AVERAGE:0.5:%d:744" % (3600 / refresh),   # 31 days of 1 hour averages
                           "RRA:AVERAGE:0.5:%d:730" % (43200 / refresh))  # 365 days of 1/2 day averages

    def __str__(self):
        return self.name

    def update(self, v_in, v_out):
        """Update the historical data."""
        rrdtool.update(self.database,
                       "--template", "v_in:v_out",
                       "N:%f:%f" % (v_in, v_out))

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
                          "--title", "%s - power signal" % self.name,
                          "--lazy",
                          "--base", "1000",
                          "--height", height,
                          "--width", width,
                          "--lower-limit", "0",
                          "--upper-limit", "1.0",
                          "--imgformat", "PNG",
                          "--vertical-label", "Volts (V)",
                          "--color", "BACK%s" % background,
                          "--color", "SHADEA%s" % border,
                          "--color", "SHADEB%s" % border,
                          "DEF:in=%s:v_in:AVERAGE" % self.database,
                          "DEF:out=%s:v_out:AVERAGE" % self.database,
                          "AREA:in#a0df05:Input Voltage",
                          "GPRINT:in:LAST:\\: %9.1lf V (now)",
                          "GPRINT:in:MAX:%9.1lf V (max)",
                          "GPRINT:in:MIN:%9.1lf V (min)\\n",
                          "LINE1:out#808080:Output Voltage",
                          "GPRINT:out:LAST:\\: %9.1lf V (now)",
                          "GPRINT:out:MAX:%9.1lf V (max)",
                          "GPRINT:out:MIN:%9.1lf V (min)")
                          
    def make_html(self):
        """Generate the HTML pages."""
        template = DetailsPage()
        template_fill(template, "Status detail for " + self.name)
        template_write(template, self.graphs_dir + "/index.html")

        
# EOF - ups.py
