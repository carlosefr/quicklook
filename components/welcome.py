#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# welcome.py - the welcome page (with some data)
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


"""Welcome Page."""


import os

from components.common import *
from templates.welcome.index import index as WelcomePage


#
# The file where we get our data from.
#
DATA_SOURCE = "/proc/uptime"


class Welcome(StatsComponent):
    """Welcome Page."""
    def __init__(self, components):
        self.components = components
        self.uptime = 0.0
        
        self.name = "welcome"

        if not os.path.exists(DATA_SOURCE):
            fail(self.name, "cannot find \"%s\"." % DATA_SOURCE)
            raise StatsException(DATA_SOURCE + " does not exist")
        
        self.title = "Welcome"
        self.description = "Welcome Page"

        self.output_dir = properties["output"]

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def info(self):
        """Return some information about the component,
           as a tuple: (name, title, description)"""
        return (self.name, self.title, self.description)

    def update(self):
        """Update the dynamic data."""
        f = open(DATA_SOURCE, "r")
        
        data = f.readline().split()
        self.uptime = float(data[0])

        f.close()

    def make_html(self):
        """Generate the HTML pages."""
        template = WelcomePage()
        template.components = [component.info() for component in self.components]
        
        # Convert uptime from seconds to days, hours and minutes.
        tmp = self.uptime / (60 * 60 * 24)
        days = int(tmp)
        tmp = (tmp - days) * 24
        hours = int(tmp)
        tmp = (tmp - hours) * 60
        minutes = int(tmp)
        
        template.uptime = "%d day(s), %d hour(s), %d minute(s)" % (days, hours, minutes)        
        
        template_fill(template, "available statistics components", True)
        template_write(template, self.output_dir + "/index.html")

        
# EOF - welcome.py
