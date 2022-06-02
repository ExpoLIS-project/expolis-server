#!/usr/bin/env python3

import os.path
import posix_ipc
from typing import TextIO
import yaml

import command
import database
import log
from interpolation import INTERPOLATION_RESOLUTION


def main (fd_log: TextIO):
    with open ('/opt/expolis/etc/config-osrm', 'r') as fd_config_osrm:
        config = yaml.safe_load (fd_config_osrm)
    mutex = posix_ipc.Semaphore (
        name=config ['mutex'],
    )
    mutex.acquire ()
    # download Open Street Map data
    command.run_command (
        command_line=[
            '/usr/bin/curl',
            config ['map_url'],
            '--silent',
            '--show-error',
            '--output', config ['map_path']
        ],
        fd_log=fd_log,
    )
    # update osm_data database
    # noinspection SpellCheckingInspection
    command.run_command (
        command_line=[
            '/usr/bin/osm2pgsql',
            '--create',
            '--input-reader', 'pbf',
            '--latlong',
            '--database', database.DATABASE_OSM,
            '--username', database.ROLE_ADMIN,
            '--prefix', 'region_osm',
            config ['map_path']
        ],
        fd_log=fd_log
    )
    # compute extent of OSM
    db = database.Database (database=database.DATABASE_OSM)
    # language=sql
    sql_statement = '''
SELECT ST_XMin (q2.bd), ST_YMin (q2.bd), ST_XMax (q2.bd), ST_YMax (q2.bd) FROM (
SELECT ST_EXTENT (way) AS bd FROM (
        SELECT way FROM region_osm_line
UNION   SELECT way FROM region_osm_point
UNION   SELECT way FROM region_osm_polygon
UNION   SELECT way FROM region_osm_roads
) AS q1
) AS q2
'''
    db.cursor.execute (sql_statement)
    row = db.cursor.fetchone ()
    # write raster configuration
    min_longitude, min_latitude, max_longitude, max_latitude = row
    grid_cell_size = min (INTERPOLATION_RESOLUTION.cell_latitude_size, INTERPOLATION_RESOLUTION.cell_longitude_size)
    num_rows = int ((max_latitude - min_latitude) / grid_cell_size) + 1
    num_cols = int ((max_longitude - min_longitude) / grid_cell_size) + 1
    with open ('/opt/expolis/etc/config-osrm-raster', 'w') as fd_cfg:
        fd_cfg.write ('''\
{min_longitude} {min_latitude}
{max_longitude} {max_latitude}
{num_rows} {num_cols}
0.5 0.5
{grid_cell_size}
'''.format (
            min_longitude=min_longitude,
            min_latitude=min_latitude,
            max_longitude=max_longitude,
            max_latitude=max_latitude,
            num_rows=num_rows,
            num_cols=num_cols,
            grid_cell_size=grid_cell_size,
        ))

    mutex.release ()
    # update data used by the OSRM engines that DO NOT DEPEND on pollution
    for a_routing in config ['routing']:
        if a_routing ['pollution'] is not None:
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


with open ('/var/log/expolis/download-routing-data', 'a') as fd:
    log.log (fd, 'start')
    main (fd)
    log.log (fd, 'end')
