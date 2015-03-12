# <font color='red'>This project is no longer maintained!</font> #

It may still be useful, but will no longer be updated.

# What is it? #

_Quick Look_ is a package to collect system statistics and output pretty graphics and (X)HTML pages. It allows system administrators to have a quick look on the status of their systems, without going for a more advanced (and heavier) solution.

_Quick Look_ currently shows...

  * CPU and memory usage
  * Load average and process spawning rates
  * I/O operations
  * Network traffic rates
  * Tracked network connections

# What does it need to run? #

  * [Python](http://www.python.org/) 2.3 or newer
  * [Cheetah](http://www.cheetahtemplate.org/) 0.9.16 or newer
  * Linux 2.4.27 or newer, 2.6.8 or newer
  * [rrdtool](http://oss.oetiker.ch/rrdtool/) 1.0.49 or newer
  * python-rrd 0.2.1 or newer

Older versions of any of these packages may work, but haven't been tested. Newer versions should also work, and you should use them if possible. If you notice any problems, please [file a bug report](http://code.google.com/p/quicklook/issues/entry) and I'll try to fix them.

# Installation #

To install _Quick Look_ into `/opt/quicklook`, just run the following commands:

  1. `make DESTDIR=/opt/quicklook install`
  1. `cp extras/quicklook.cron /etc/cron.d/stats`

By default, data files are stored in `/var/opt/quicklook` and webpages are generated into the `/var/www/quicklook` directory. If you wish to make changes to the output directories, or you chose a different installation directory, edit the `quicklook.cron` file before copying it.

_Quick Look_ will now collect data and generate webpages every five minutes. No other steps are needed, but you can always run `stats.py` without parameters to check out the options available.

# Upgrade from 1.0.x #

When using _Quick Look_ 1.0.x, a reboot could cause some of the graphs to have a
huge spike. To prevent this from happening, the format for some of the data
files (`*.rrd`) had to be changed.

Newer versions of _Quick Look_ cannot read these files, and they have to be
converted if you wish to keep the data contained in them. To do this, you can
use the `extras/convert.sh` script.

For example, if you are storing data files in `/var/opt/quicklook` (default),
they can be converted with the following command:

> `convert.sh /var/opt/quicklook`

Backup this directory first, just in case.

# Releases #

| **Date** | **Version** | **Changes** |
|:---------|:------------|:------------|
| 2008-04-12 | [1.1](http://quicklook.googlecode.com/files/quicklook-1.1.tar.gz) | Fixed problem with occasional huge spikes in graphs after rebooting, but existing data files must be converted (see: _Upgrade from 1.0.x_). |
| 2007-12-01 | ~~1.0.2~~   | Fixed problems with disk devices with slashes in their names (e.g. HP SmartArray RAID volumes). |
| 2006-12-17 | ~~1.0.1~~   | Fixed problems with [dhttpd](http://dhttpd.sourceforge.net). Automatic refresh for statistics pages. New color scheme for graphs. |
| 2006-09-02 | ~~1.0a~~    | Fixed problem with rrdtool 1.2.x. |
| 2006-09-01 | ~~1.0~~     | Initial public release. |