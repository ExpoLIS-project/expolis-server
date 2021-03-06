#!/usr/bin/env python3

import argparse
import datetime
import os.path
import sys

import data
from database import Database


__DATETIME_FORMAT_CSV__ = '%Y-%m-%dT%H:%M:%S'
__DATETIME_FORMAT_SQL__ = '%Y-%m-%d %H:%M:%S.%f'


class Args:
    def __init__ (self):
        parser = argparse.ArgumentParser (
            description='Compare the data in a CSV file generated by a sensor node with the data stored in '
                        'the ExpoLIS database'
        )
        parser.add_argument (
            'sensor_node',
            metavar='ID',
            type=int,
            help='Unique integer that identifies the sensor node',
        )
        parser.add_argument (
            'csv_file',
            metavar='FILENAME',
            type=str,
            help='CSV file to analyse',
        )
        parser.add_argument (
            '--report',
            action='store_true',
            help='Just print a report with data mismatch',
        )
        args = parser.parse_args ()
        self.sensor_node_id = args.sensor_node  # type: int
        self.csv_file = args.csv_file           # type: str
        self.report = args.report               # type: bool


def main ():
    args = Args ()
    csv_file = args.csv_file
    if not os.path.exists (csv_file):
        print ('File {} does not exist!'.format (csv_file))
        sys.exit (1)
    if not os.path.isfile (csv_file):
        print ('File {} is not a regular file!'.format (csv_file))
        sys.exit (2)
    data.load_data ()
    db = Database ()
    try:
        with open (csv_file, 'rt') as fd:
            process_file (args.sensor_node_id, csv_file, db, fd)
    except OSError:
        print ('Could not open file {}!.'.format (csv_file))
        sys.exit (3)


def process_file (sensor_node_id: int, csv_file_name: str, db: Database, fd):
    # CSV files generated by sensor nodes have two header rows
    fd.readline ()
    fd.readline ()
    number_rows = 0
    number_missing_data = 0
    for line in fd:
        row = line.replace (',', '.')
        row = row.split (' ')
        number_rows += 1
        when = datetime.datetime.strptime (row [1], __DATETIME_FORMAT_CSV__)\
            .strftime (__DATETIME_FORMAT_SQL__)
        latitude = row [2]
        longitude = row [3]
        # language=SQL
        sql_statement = '''
SELECT COUNT (*)
 FROM measurement_properties INNER JOIN node_sensors ON 
   measurement_properties.nodeID = node_sensors.ID
  WHERE node_sensors.mqtt_topic_number = CAST (%s AS INTEGER)
   AND when_ = CAST (%s AS TIMESTAMP)
   AND latitude = CAST (%s AS DOUBLE PRECISION) 
   AND longitude = CAST (%s AS DOUBLE PRECISION) 
      '''
        db.cursor.execute (sql_statement, (sensor_node_id, when, latitude, longitude))
        result = db.cursor.fetchone ()
        if result [0] == 0:
            number_missing_data += 1
    if number_missing_data == 0:
        print ('All data in CSV file {} is in the database.'.format (csv_file_name))
    elif number_missing_data == number_rows:
        print ('All rows from CSV file are not in the database!'.format (
            csv_file_name
        ))
    else:
        print ('{} rows ({:.1f}%) out of {} from CSV file {} are not in the database!'.format (
            number_missing_data,
            number_missing_data * 100 / number_rows,
            number_rows,
            csv_file_name
        ))
    return number_missing_data == 0


if __name__ == '__main__':
    main ()
