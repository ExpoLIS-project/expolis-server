#!/usr/bin/env python3

import datetime
import os.path
import posix_ipc
from typing import TextIO, Dict, Tuple, List
import yaml

import command
import log
import data
import osrm_raster
from database import Database
from interpolation_method import METHODS
from interpolation_period import PeriodDaily


def main (fd_log: TextIO):
    data.load_data ()
    config_osrm_raster = osrm_raster.load_config_osrm_raster ()
    has_data, pollution_data = read_pollution_data (fd_log, config_osrm_raster)
    if has_data:
        create_raster_image (fd_log, config_osrm_raster, pollution_data)
    else:
        create_empty_raster_image (fd_log, config_osrm_raster)
    update_routing_data (fd_log)


def read_pollution_data (fd_log: TextIO, config_osrm_raster: osrm_raster.ConfigOSRMRaster) -> Tuple[bool, Dict]:
    db = Database ()
    now = datetime.datetime.now ()
    when = datetime.datetime (
        year=now.year,
        month=now.month,
        day=now.day
    ) - datetime.timedelta (days=1)
    period = PeriodDaily (when)
    matrix_data_raw = {}
    for a_method in METHODS:
        matrix_data_raw [a_method.sql_identifier] = {}
        for a_data in data.DATA:
            if a_data.route_planner_flag:
                log.log (fd_log, '  {:10s} {:30s}'.format (
                    a_method.description,
                    a_data.description_en))
                table_name = a_data.table_interpolation_name (
                    m=a_method,
                    p=period.enum,
                )
                sql_statement = '''
SELECT value
   FROM {table_name}
   WHERE when_ >= %s AND when_ < %s
   ORDER BY ST_X (longLat), ST_Y (longLat)
       '''.format (table_name=table_name)
                db.cursor.execute (
                    sql_statement,
                    (period.start, period.end)
                )
                xs = [row[0] for row in db.cursor]
                n = len (xs)
                if n == config_osrm_raster.num_rows * config_osrm_raster.num_cols:
                    matrix_data_raw [a_method.sql_identifier][a_data.sql_identifier] = xs
                else:
                    if n != 0:
                        log.log (fd_log, ' ERROR: there are {} values'.format (n))
                    return False, {}
    return True, matrix_data_raw


def create_raster_image (
        fd_log: TextIO,
        config_osrm_raster: osrm_raster.ConfigOSRMRaster,
        pollution_data: Dict[str, Dict[str, List[int]]]):
    i = 0
    log.log (fd_log, 'start creating raster image')
    with open ('/var/lib/expolis/osrm/pollution-sensor.raster', 'w') as fd_pollution:
        for x in range (config_osrm_raster.num_cols):
            for y in range (config_osrm_raster.num_rows):
                best_value = 0
                for a_method in METHODS:
                    for a_data in data.DATA:
                        if not a_data.route_planner_flag:
                            continue
                        x = pollution_data [a_method.sql_identifier][a_data.sql_identifier][i]
                        this_value = a_data.pollution_profile_m * x + a_data.pollution_profile_b
                        if this_value > best_value:
                            best_value = this_value
                fd_pollution.write (str (best_value))
                fd_pollution.write (' ')
                i += 1
            fd_pollution.write ('\n')
    log.log (fd_log, 'end creating raster image')


def create_empty_raster_image (
    fd_log: TextIO,
    config_osrm_raster: osrm_raster.ConfigOSRMRaster,
):
    log.log (fd_log, 'empty raster image')
    with open ('/var/lib/expolis/osrm/pollution-sensor.raster', 'w') as fd_pollution:
        for x in range (config_osrm_raster.num_cols):
            for y in range (config_osrm_raster.num_rows):
                fd_pollution.write ('0 ')
            fd_pollution.write ('\n')


def update_routing_data (fd_log: TextIO):
    with open ('/opt/expolis/etc/config-osrm', 'r') as fd_config_osrm:
        config = yaml.safe_load (fd_config_osrm)
    mutex = posix_ipc.Semaphore (
        name=config ['mutex'],
    )
    mutex.acquire ()
    for a_routing in config ['routing']:
        if not a_routing ['pollution'] == 'sensor':
            continue
        # path to the symbolic link in the folder where this profile files are stored
        map_path = os.path.join (a_routing ['folder'], os.path.basename (config ['map_path']))
        log.log (fd_log, 'Processing LUA profile {} in folder {}'.format (
            a_routing ['profile'],
            a_routing ['folder'],
        ))
        command.run_command (
            command_line=[
                '/usr/local/bin/osrm-extract',
                map_path,
                '--profile', a_routing ['profile']
            ],
            fd_log=fd_log,
        )
        command.run_command (
            command_line=[
                '/usr/local/bin/osrm-partition',
                map_path,
            ],
            fd_log=fd_log,
        )
        command.run_command(
            command_line=[
                '/usr/local/bin/osrm-customize',
                map_path,
            ],
            fd_log=fd_log
        )
        command.run_command(
            command_line=[
                '/usr/local/bin/osrm-contract',
                map_path,
            ],
            fd_log=fd_log
        )
    mutex.release ()


with open ('/var/log/expolis/update-routing-data', 'a') as fd:
    log.log (fd, 'start')
    main (fd)
    log.log (fd, 'end')
