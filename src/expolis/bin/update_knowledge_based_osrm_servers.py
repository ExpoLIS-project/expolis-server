#!/usr/bin/env python3

import argparse
import os.path
import shutil
import subprocess
import sys

import posix_ipc
import yaml

import osrm_raster


class Args:
    def __init__ (self):
        parser = argparse.ArgumentParser (
            description='Update the knowledge based OSRM servers. Processes a raster image and invokes the OSRM tool '
                        'chain. '
        )
        parser.add_argument (
            'raster',
            metavar='FILENAME',
            type=str,
            help='Filename with raster image'
        )
        result = parser.parse_args ()
        self.raster = result.raster


def main ():
    args = Args ()
    if __check_file__ (args.raster):
        subprocess.run (
            args=[
                '/etc/init.d/expolis_osrm_server',
                'stop',
            ],
        )
        __update_osrm_data__ (args.raster)
        subprocess.Popen (
            args=[
                '/etc/init.d/expolis_osrm_server',
                'start',
            ],
        )
    else:
        sys.exit (1)


def __check_file__ (raster: str):
    if os.path.exists (raster):
        count = 0
        lines = 0
        with open (raster, 'r') as fd:
            for line in fd:
                count += len (line.split (' '))
                lines += 1
        config_osrm_raster = osrm_raster.load_config_osrm_raster ()
        value = config_osrm_raster.num_cols * config_osrm_raster.num_rows
        if value == count and lines == config_osrm_raster.num_rows:
            return True
        else:
            print (
                'File {} should have {} lines each with {} values. '
                'Instead the file has {} lines and a total of {} values'.format (
                    raster,
                    config_osrm_raster.num_rows,
                    config_osrm_raster.num_cols,
                    lines,
                    count
                ))
            return False
    else:
        print ('File {} does not exist!'.format (raster))
        return False


def __update_osrm_data__ (raster: str):
    shutil.copy (
        src=raster,
        dst='/var/lib/expolis/osrm/pollution-knowledge.raster'
    )
    with open ('/opt/expolis/etc/config-osrm', 'r') as fd_config_osrm:
        config = yaml.safe_load (fd_config_osrm)
    mutex = posix_ipc.Semaphore (
        name=config ['mutex'],
    )
    mutex.acquire ()
    for a_routing in config ['routing']:
        if not a_routing ['pollution'] == 'knowledge':
            continue
        # path to the symbolic link in the folder where this profile files are stored
        map_path = os.path.join (a_routing ['folder'], os.path.basename (config ['map_path']))
        print ('Processing LUA profile {} in folder {}'.format (
            a_routing ['profile'],
            a_routing ['folder'],
        ))
        subprocess.run (
            args=[
                '/usr/local/bin/osrm-extract',
                map_path,
                '--profile', a_routing ['profile']
            ],
        )
        subprocess.run (
            args=[
                '/usr/local/bin/osrm-partition',
                map_path,
            ],
        )
        subprocess.run (
            args=[
                '/usr/local/bin/osrm-customize',
                map_path,
            ],
        )
        subprocess.run (
            args=[
                '/usr/local/bin/osrm-contract',
                map_path,
            ],
        )
    mutex.release ()


if __name__ == '__main__':
    main ()
