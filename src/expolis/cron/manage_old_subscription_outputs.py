#!/usr/bin/env python3
"""
This cron script goes through all CSV files that are in the WWW server, and deletes old files.

Subscribers have a few days to download CSV data they subscribed.
"""

import datetime
import os

DATA_SET_FOLDER = '/var/www/html/dataset'
DATA_SET_EXPIRE = 3
DATA_SET_PREFIX = 'data-request_'


def main ():
    now = datetime.datetime.now ()
    span_expire = datetime.timedelta (days=DATA_SET_EXPIRE)
    for entry in os.scandir (DATA_SET_FOLDER):
        if entry.name.startswith (DATA_SET_PREFIX) and \
                entry.is_file () and \
                entry.stat ().st_birthtime + span_expire < now:
            os.remove (os.path.join (DATA_SET_FOLDER, entry.name))


if __name__ == '__main__':
    main ()
