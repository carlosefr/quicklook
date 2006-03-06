#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
# 
# common.py - commmon component code
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


"""Definitions common to all statistics components, like base classes, etc."""


NAME="Quick Look"
VERSION="1.0"


import sys

from socket import getfqdn
from time import time, localtime, strftime


#
# The global properties dictionary.
# 
# We give some default values to the
# properties that must always exist.
#
properties = { "data"       : "./data",   # base directory for the data files.
               "output"     : "./stats",  # base directory for the graphics.
               "refresh"    : 300,        # refresh interval, in seconds.
               "width"      : 600,        # width for all the graphics.
               "height"     : 120,        # height for all the graphics.
               "background" : "#e9e7dd",  # background color for the graphics.
               "border"     : "#e9e7dd",  # border color for the graphics.
               "verbose"    : False }     # be verbose or silent.
               

class StatsError(Exception):
    """Unrecoverable error."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

        
class StatsException(Exception):
    """Recoverable error."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
    

#
# All components inherit from the StatsComponent class.
#
# As a rule, all components must store their output on a directory
# named after the component, as returned by the info() method.
#
class StatsComponent(object):
    """Abstract base class for all components."""
    def info(self):
        """Return some information about the component,
           as a tuple: (name, title, description)"""
        raise NotImplementedError, "method not implemented"

    def update(self):
        """Update the component's data."""
        raise NotImplementedError, "method not implemented"

    def make_graphs(self):
        """Generate the graphics from the component's data."""
        raise NotImplementedError, "method not implemented"

    def make_html(self):
        """Generate the HTML pages for the component."""
        raise NotImplementedError, "method not implemented"


def fail(component, reason):
    """Print a reason why a component can't be loaded."""
    if properties["verbose"]:
        sys.stderr.write("Cannot start component \"%s\": %s" % (component, reason))
        

#
# Template helper functions.
#

def template_fill(template, description, is_toplevel=False):
    """Fill the common parts of the template."""
    template.name = NAME
    template.hostname = getfqdn()
    template.version = VERSION
    template.time = strftime("%B %d, %Y - %H:%M:%S", localtime(time()))
    template.description = description
    template.is_toplevel = is_toplevel


def template_write(template, filename):
    """Write the template to a file."""
    f = open(filename, "w")
    f.write(str(template))
    f.close()


# EOF - common.py
