> This project is no longer being maintained.

Quick Look
==========

Quick Look is a package to collect system statistics and output pretty graphics
and (X)HTML pages. It allows system administrators to have a quick look on the
status of their systems, without going for a more advanced (and heavier)
solution.

Quick Look currently shows...

  * CPU and memory usage
  * Load average and process spawning rates
  * I/O operations
  * Network traffic rates
  * Tracked network connections


Requirements
============

  * Python 2.3 or newer
  * Cheetah 0.9.16 or newer
  * Linux 2.4.27 or newer, 2.6.8 or newer
  * rrdtool 1.0.49 or newer
  * python-rrd 0.2.1 or newer

Older versions of any of these packages may work, but haven't been tested.


Installation
============

To install Quick Look into "/opt/quicklook", just run the following commands:

    make DESTDIR=/opt/quicklook install
    cp extras/quicklook.cron /etc/cron.d/quicklook

By default, data files are stored in `/var/opt/quicklook` and webpages are
generated into the `/var/www/quicklook` directory. If you wish to make changes
to the output directories, or you chose a different installation directory, edit
the `quicklook.cron` file before copying it.

Quick Look will now collect data and generate webpages every five minutes. No
other steps are needed, but you can always run `stats.py` without parameters to
check out the options available.
