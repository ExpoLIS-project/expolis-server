#!/usr/bin/env python3

"""
When a new sensor data is added to the database, we have to:

* create the table that holds measurements;
* create the functions that compute graph data, if the sensor data is going to be displayed in the mobile app;
* create the table that holds aggregate data, if the sensor data is going to be displayed in the mobile app;
* create the table that holds interpolation data, if the sensor data is to be used in the route planner;
* add a column in the subscriptions table, if a user can subscribe to receive new sensor data;
"""
import argparse
import subprocess
import sys
from typing import Optional

import data
import interpolation_method
from interpolation import INTERPOLATION_PERIOD, INTERPOLATION_RESOLUTION, INTERPOLATION_STATISTIC
import period
import resolution
import aggregation

DATABASE = 'sensor_data'
ROLE_ADMIN = 'expolis_admin'
ROLE_APP = 'expolis_app'
ROLE_PHP = 'expolis_php'


def main ():
    args = process_arguments ()
    new_sensor_data (
        sql_identifier=args.identifier,
        sql_type=args.type,
        description_en=input('English description? '),
        description_pt=input('Portuguese description? '),
        pollution_profile_b=args.pollution_profile_b,
        pollution_profile_m=args.pollution_profile_m,
        mobile_app_flag=args.mobile_app,
        route_planner_flag=args.pollution_profile_b is not None and args.pollution_profile_b is not None,
        subscribe_flag=args.subscribe,
        mqtt_message_index=args.mqtt_message_index,
    )
    print (args)


def new_sensor_data (
        sql_identifier: str,
        sql_type: str,
        description_en: str,
        description_pt: str,
        pollution_profile_m: Optional [float],
        pollution_profile_b: Optional [float],
        mobile_app_flag: bool,
        route_planner_flag: bool,
        subscribe_flag: bool,
        mqtt_message_index: Optional[int],
):
    if (pollution_profile_b is None and pollution_profile_m is not None) or \
            (pollution_profile_b is not None and pollution_profile_m is None):
        print ('Specify both pollution profile constants or leave them as None')
        return False
    data.load_data ()
    for a_data in data.DATA:
        if a_data.sql_identifier == sql_identifier:
            print ('There is already a sensor data with name {}!'.format (sql_identifier))
            return False
    new_data = data.Data (
        sql_identifier=sql_identifier,
        description_en=description_en,
        description_pt=description_pt,
        sql_type=sql_type,
        mqtt_message_index=len (data.DATA) if mqtt_message_index is None else mqtt_message_index,
        pollution_profile_b=pollution_profile_b,
        pollution_profile_m=pollution_profile_m,
        mobile_app_flag=mobile_app_flag,
        route_planner_flag=route_planner_flag,
        subscribe_flag=subscribe_flag,
    )
    # if mqtt_message_index is not None:
    #     for d in data.DATA:
    #         if d.mqtt_message_index >= mqtt_message_index:
    #             d.mqtt_message_index += 1
    # region create tables
    sql_commands = '''
CREATE TABLE {table_measurement} (
       mpID INTEGER PRIMARY KEY REFERENCES measurement_properties (ID) ON DELETE CASCADE,
       value {sql_type} NOT NULL
);
'''.format (
        table_measurement=new_data.table_measurement_name (),
        sql_type=sql_type,
    )
    if mobile_app_flag or route_planner_flag:
        for s in aggregation.STATISTICS:
            if not mobile_app_flag and (not route_planner_flag or s != INTERPOLATION_STATISTIC):
                continue
            for p in period.PERIODS:
                if not mobile_app_flag and (not route_planner_flag or p != INTERPOLATION_PERIOD):
                    continue
                for r in resolution.RESOLUTIONS:
                    if not mobile_app_flag and (not route_planner_flag or r != INTERPOLATION_RESOLUTION):
                        continue
                    sql_commands += '''
CREATE TABLE {table_name} (
    long_lat GEOMETRY (POINT) NOT NULL,
    value {sql_type},
    when_ TIMESTAMP,
    UNIQUE (long_lat, when_)
);
'''.format (
                        table_name=new_data.table_aggregation_name (s, p, r),
                        sql_type=s.sql_type (new_data.sql_type),
                    )
    if mobile_app_flag or route_planner_flag:
        for m in interpolation_method.METHODS:
            for p in period.PERIODS:
                if not mobile_app_flag and route_planner_flag and p != INTERPOLATION_PERIOD:
                    continue
                sql_commands += '''
CREATE TABLE {} (
    longLat GEOMETRY,
    value DOUBLE PRECISION,
    when_ TIMESTAMP,
    UNIQUE (longLat, when_)
);
'''.format (
                    new_data.table_interpolation_name (m, p)
                )
    # endregion
    # region subscriptions
    if subscribe_flag:
        sql_commands += '''
ALTER TABLE subscriptions
    ADD COLUMN {sql_identifier} BOOLEAN NOT NULL DEFAULT false;
'''.format (
            sql_identifier=new_data.sql_identifier,
        )
    # endregion
    # region create functions aggregate
    if mobile_app_flag or route_planner_flag:
        for s in aggregation.STATISTICS:
            if not (mobile_app_flag or (route_planner_flag and s == INTERPOLATION_STATISTIC)):
                continue
            for p in period.PERIODS:
                if not (mobile_app_flag or (route_planner_flag and p == INTERPOLATION_PERIOD)):
                    continue
                for r in resolution.RESOLUTIONS:
                    if not (mobile_app_flag or (route_planner_flag and r == INTERPOLATION_RESOLUTION)):
                        continue
                    sql_commands += '''
CREATE FUNCTION
 aggregate_{statistic_sql_identifier}_{period_sql_identifier}_{resolution_sql_identifier}_{data_sql_identifier} (
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
) RETURNS void
LANGUAGE sql
AS $$
INSERT INTO {table_aggregation} (long_lat, value, when_)
SELECT
    ST_SetSRID (ST_MakePoint (longitude, latitude), 4326), {sql_function} (value), from_date
FROM (
  SELECT
    {cell_longitude_size} * round (ST_X (long_lat) / {cell_longitude_size}) AS longitude,
    {cell_latitude_size} * round (ST_Y (long_lat) / {cell_latitude_size}) AS latitude,
    value
  FROM measurement_properties
  INNER JOIN {table_measurement}
     ON measurement_properties.ID = {table_measurement}.mpID
  WHERE when_ >= from_date AND when_ < to_date
  ) AS sq
  GROUP BY longitude, latitude
$$;
'''.format (
                        statistic_sql_identifier=s.sql_function,
                        period_sql_identifier=p.sql_identifier,
                        resolution_sql_identifier=r.sql_identifier,
                        data_sql_identifier=new_data.sql_identifier,
                        table_aggregation=new_data.table_aggregation_name (s, p, r),
                        table_measurement=new_data.table_measurement_name (),
                        sql_function=s.sql_function,
                        cell_latitude_size=r.cell_latitude_size,
                        cell_longitude_size=r.cell_longitude_size,
                    )

    # endregion
    # region create functions graph
    if mobile_app_flag:
        for s in aggregation.STATISTICS:
            sql_commands += '''
CREATE FUNCTION graph_map_data_raw_{sql_function}_{sql_identifier} (
    IN cell_size REAL,
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
RETURNS TABLE (longitude double precision, latitude double precision, value {sql_type})
LANGUAGE sql
AS $$
SELECT longitude, latitude, {sql_function} (value) AS value
FROM (
  SELECT
    cell_size * round (ST_X (long_lat) / cell_size) AS longitude,
    cell_size * round (ST_Y (long_lat) / cell_size) AS latitude,
    value
  FROM measurement_properties
  INNER JOIN {table_measurement}
     ON measurement_properties.ID = {table_measurement}.mpID
  WHERE when_ >= from_date AND when_ <= to_date
  ) AS sq
  GROUP BY longitude, latitude
$$;

CREATE FUNCTION graph_cell_data_raw_{sql_function}_{sql_identifier} (
    IN the_longitude DOUBLE PRECISION,
    IN the_latitude DOUBLE PRECISION,
    IN cell_radius REAL,
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
RETURNS TABLE (when_ timestamp, value {sql_type})
LANGUAGE sql
AS $$
SELECT when_, {sql_function} (value) AS value
  FROM (
    SELECT
      date_trunc ('hour', when_) AS when_,
      value
    FROM measurement_properties
    INNER JOIN {table_measurement}
    ON measurement_properties.ID = {table_measurement}.mpID
    WHERE
      when_ >= from_date
      AND when_ <= to_date
      AND ST_DistanceSphere (long_lat, ST_SetSRID (ST_MakePoint (the_longitude, the_latitude), 4326)) <= cell_radius
    ) AS sq
  GROUP BY when_
$$;

CREATE FUNCTION graph_line_data_raw_{sql_function}_{sql_identifier} (
    IN line_id INTEGER,
    IN cell_radius REAL,
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
RETURNS TABLE (longitude double precision, latitude double precision, value {sql_type})
LANGUAGE sql
AS $$
SELECT ST_X (line_path.long_lat), ST_Y (line_path.long_lat), {sql_function} (value) AS value
    FROM line_path
    INNER JOIN measurement_properties
    ON ST_DistanceSphere (line_path.long_lat, measurement_properties.long_lat) <= cell_radius
    INNER JOIN {table_measurement}
    ON measurement_properties.ID = {table_measurement}.mpID
    WHERE
      when_ >= from_date
      AND when_ <= to_date
      AND line_path.lineID = line_id
    GROUP BY line_path.long_lat
$$;
'''.format (
                sql_identifier=new_data.sql_identifier,
                sql_function=s.sql_function,
                sql_type=s.sql_type (new_data.sql_type),
                table_measurement=new_data.table_measurement_name (),
            )
        for m in interpolation_method.METHODS:
            for p in period.PERIODS:
                # noinspection SpellCheckingInspection
                sql_commands += '''
CREATE FUNCTION graph_interpolated_data_map_{method_sql_identifier}_{period_sql_identifier}_{data_sql_identifier} (
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
RETURNS TABLE (longitude DOUBLE PRECISION, latitude DOUBLE PRECISION, value DOUBLE PRECISION)
LANGUAGE sql
AS $$
SELECT
    ST_X (longlat) AS longitude, ST_Y (longlat) AS latitude, AVG (value) AS VALUE
FROM {table_interpolation}
WHERE
    when_ >= from_date
    AND when_ <= to_date
GROUP BY
    longlat
$$;
'''.format (
                    method_sql_identifier=m.sql_identifier,
                    period_sql_identifier=p.sql_identifier,
                    data_sql_identifier=new_data.sql_identifier,
                    table_interpolation=new_data.table_interpolation_name (m, p)
                )
    # endregion
    # region function insert measurement
    sql_commands += 'DROP FUNCTION insert_measurements (INTEGER, TIMESTAMP, REAL, DOUBLE PRECISION, DOUBLE PRECISION'
    for d in data.DATA:
        sql_commands += ', {sql_type}'.format (sql_type=d.sql_type)
    sql_commands += ''');
CREATE FUNCTION insert_measurements (
    IN mqtt_topic INTEGER,
    IN date_time TIMESTAMP,
    IN gps_error REAL,
    IN longitude DOUBLE PRECISION,
    IN latitude DOUBLE PRECISION'''
    for d in data.DATA + [new_data]:
        sql_commands += ''',
    IN {sql_identifier} {sql_type} DEFAULT NULL'''.format (
            sql_identifier=d.sql_identifier,
            sql_type=d.sql_type,
        )
    # noinspection SpellCheckingInspection
    sql_commands += '''
) RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    mpid integer;
    node_id integer;
BEGIN
    node_id := (SELECT ID FROM node_sensors WHERE mqtt_topic_number = mqtt_topic);
    INSERT INTO
        measurement_properties (nodeID, when_, gps_error, longitude, latitude, long_lat)
    VALUES
        (node_id, date_time, gps_error, longitude, latitude, ST_SetSRID (ST_MakePoint (longitude, latitude), 4326));
    mpid := currval ('measurement_properties_ID_seq');'''
    for d in data.DATA + [new_data]:
        # noinspection SpellCheckingInspection
        sql_commands += '''
        IF NOT {sql_identifier} IS NULL THEN
            INSERT INTO {table_measurement} (mpID, value) VALUES
            (mpid, {sql_identifier});
        END IF;'''.format (
            sql_identifier=d.sql_identifier,
            table_measurement=d.table_measurement_name (),
        )
    sql_commands += '''
END;
$$;
'''
    # endregion
    # region grant permissions
    if mobile_app_flag:
        sql_commands += '''
GRANT SELECT ON TABLE aggregation_avg_daily_hundred_meters_{sql_identifier} TO {role_app};
GRANT SELECT ON TABLE {table_measurement} TO {role_app};
'''.format (
            table_measurement=new_data.table_measurement_name (),
            sql_identifier=new_data.sql_identifier,
            role_app=ROLE_APP,
        )
        for s in aggregation.STATISTICS:
            sql_commands += '''
GRANT EXECUTE ON FUNCTION graph_map_data_raw_{sql_function}_{sql_identifier} (
    IN cell_size REAL,
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
TO {role_app};

GRANT EXECUTE ON FUNCTION graph_cell_data_raw_{sql_function}_{sql_identifier} (
    IN longitude DOUBLE PRECISION,
    IN latitude DOUBLE PRECISION,
    IN cell_radius REAL,
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
TO {role_app};

GRANT EXECUTE ON FUNCTION graph_line_data_raw_{sql_function}_{sql_identifier} (
    IN line_id INTEGER,
    IN cell_radius REAL,
    IN from_date TIMESTAMP,
    IN to_date TIMESTAMP
)
TO {role_app};
'''.format (
                sql_identifier=new_data.sql_identifier,
                sql_function=s.sql_function,
                role_app=ROLE_APP,
            )
        for m in interpolation_method.METHODS:
            for p in period.PERIODS:
                sql_commands += '''
GRANT SELECT ON TABLE {table_interpolation} TO {role_app};
GRANT EXECUTE ON FUNCTION \
    graph_interpolated_data_map_{method_sql_identifier}_{period_sql_identifier}_{data_sql_identifier} (
        IN from_date TIMESTAMP,
        IN to_date TIMESTAMP
    )
    TO {role_app};
'''.format (
                    table_interpolation=new_data.table_interpolation_name (m, p),
                    role_app=ROLE_APP,
                    method_sql_identifier=m.sql_identifier,
                    period_sql_identifier=p.sql_identifier,
                    data_sql_identifier=new_data.sql_identifier,
                )

    if subscribe_flag:
        sql_commands += '''
GRANT SELECT ON TABLE {table_measurement} TO {role_php};
'''.format (
            table_measurement=new_data.table_measurement_name (),
            role_php=ROLE_PHP,
        )
    # endregion
    command_line = [
        '/usr/bin/sudo',
        '-u', 'postgres',
        'psql',
        '-U', ROLE_ADMIN,
        '-d', DATABASE,
    ]
    process = subprocess.Popen (
        command_line,
        stdin=subprocess.PIPE,
        universal_newlines=True,
    )
    process.communicate (sql_commands)
    return_code = process.wait ()
    if return_code != 0:
        print ('A problem occurred while creating sensor data {}!'.format (sql_identifier))
    else:
        data.DATA.append (new_data)
        data.save_data ()


def process_arguments ():
    parser = argparse.ArgumentParser (
        description='Add a new sensor data to the ExpoLIS server',
    )
    parser.add_argument (
        'identifier',
        metavar='NAME',
        type=str,
        help='Name of the sensor data. Must be a valid SQL identifier as it is used as part of the name of SQL '
             'tables, and functions',
    )
    parser.add_argument (
        'type',
        metavar='SQL',
        choices=['real'],
        help='Type of values that the sensor data can have. Must be a valid SQL type',
    )
    parser.add_argument (
        'mqtt-message-index',
        metavar='I',
        type=int,
        help='Index within the MQTT message where this sensor data is located.',
    )
    parser.add_argument (
        '--pollution-profile-m',
        type=float,
        default=None,
        help='If supplied, then the sensor data is used in the route planner.  Both pollution_profile_m and '
             'pollution_profile_b arguments must be supplied.',
    )
    parser.add_argument (
        '--pollution-profile-b',
        type=float,
        default=None,
        help='If supplied, then the sensor data is used in the route planner.  Both pollution_profile_m and '
             'pollution_profile_b arguments must be supplied.',
    )
    parser.add_argument (
        '--mobile-app',
        action='store_true',
        help='The sensor data is used by the mobile app.  This leads to the creation of functions to compute graph '
             'data, and of a table that holds aggregate data.',
    )
    parser.add_argument (
        '--subscribe-flag',
        action='store_true',
        help='Users can subscribe to receive datasets with sensor data.'
    )
    result = parser.parse_args ()
    if (result.pollution_profile_m is not None and result.pollution_profile_b is None) or \
            (result.pollution_profile_m is None and result.pollution_profile_b is not None):
        print ('Error: both options --pollution-profile-m and --pollution-profile-b must be supplied!')
        sys.exit (1)
    return result


if __name__ == '__main__':
    main ()
