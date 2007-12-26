#!/bin/bash -e
#
# convert.sh - update ".rrd" files created by Quick Look 1.0.x
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

#
# USAGE: run this script with the Quick Look data directory as a parameter and
#        all data files contained within it will be converted to the new format.
#
# EXAMPLE: ./convert.sh /var/opt/quicklook
#


if [ $# -lt 1 ]; then
	echo "USAGE: $0 <directory>"
	exit 1
fi


TARGET="$1"
RRDTOOL="$(which rrdtool)"


if [ -z "$RRDTOOL" ]; then
	echo "Error: rrdtool not found" >&2
	exit 1
fi


find "$TARGET" -name '*.rrd' | while read RRDFILE; do
	echo "Converting: $RRDFILE"
	"$RRDTOOL" dump "$RRDFILE" | sed s/COUNTER/DERIVE/g | "$RRDTOOL" restore - "${RRDFILE}.convert"
	mv "${RRDFILE}.convert" "$RRDFILE"
done


# EOF - convert.sh
