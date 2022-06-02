#!/usr/bin/python3

"""
Script to interpolate data.
"""

import datetime
import subprocess
import threading
from typing import List

import psycopg2.extensions
from typing.io import TextIO

import data
from data import Data
from database import Database
from interpolation_method import METHODS, Method
from interpolation_period import PeriodDaily
from interpolation import INTERPOLATION_RESOLUTION, INTERPOLATION_STATISTIC


class SendDataThread (threading.Thread):
    """
    Thread that sends data from the Postgres database to the interpolation process.
    """
    def __init__ (
            self,
            cursor: psycopg2.extensions.cursor,
            interpolation_process: subprocess.Popen,
            the_data: Data,
            period: PeriodDaily,
            number_rows: int,
            ):
        threading.Thread.__init__ (self)
        self.cursor = cursor
        self.interpolation_process = interpolation_process
        self.data = the_data
        self.period = period
        self.number_rows = number_rows

    def run (self):
        print ('Started send data thread')
        table_name = self.data.table_aggregation_name (
            s=INTERPOLATION_STATISTIC,
            p=PeriodDaily.enum,
            r=INTERPOLATION_RESOLUTION,
        )
        # send the number of rows
        self.interpolation_process.stdin.write ('{}\n'.format (self.number_rows))
        # send each row in a single line
        sql_statement = '''
SELECT ST_X (long_lat) AS longitude, ST_Y (long_lat), value
FROM {table_name}
WHERE when_ >= %s AND when_ < %s
        '''.format (
            table_name=table_name)
        self.cursor.execute (sql_statement, (self.period.start, self.period.end))
        while True:
            row = self.cursor.fetchone ()
            if row is not None:
                self.interpolation_process.stdin.write ('{} {} {}\n'.format (row [0], row[1], row[2]))
            else:
                self.interpolation_process.stdin.close ()
                print ('Finished sending data from table {} to interpolation process'.format (table_name))
                return


class SaveDataThread (threading.Thread):
    def __init__ (
            self,
            cursor: psycopg2.extensions.cursor,
            interpolation_process: subprocess.Popen,
            method: Method,
            period: PeriodDaily,
            the_data: Data,
            ):
        threading.Thread.__init__ (self)
        self.cursor = cursor
        self.interpolation_process = interpolation_process
        self.period = period
        self.table_name = the_data.table_interpolation_name (
            m=method,
            p=period.enum,
        )

    def run (self):
        print ('Started save data thread')
        sql_statement = '''\
INSERT INTO {} (longLat, value, when_)
  VALUES (
    ST_SetSRID (ST_MakePoint (%s, %s), 4326),
    %s,
    %s)'''.format (self.table_name)
        n = 0
        for line in self.interpolation_process.stdout:
            (longitude, latitude, value) = line.split ()
            self.cursor.execute (
                sql_statement,
                (float (longitude), float (latitude), float (value), self.period.start)
            )
            n += 1
        print ('{} rows saved in table {}.'.format (n, self.table_name))


def main (fd_log: TextIO):
    data.load_data ()
    now = datetime.datetime.now ()
    when = datetime.datetime (
        year=now.year,
        month=now.month,
        day=now.day
    ) - datetime.timedelta (days=1)
    period = PeriodDaily (when)
    fd_log.write ('{}:   interpolation period {}\n'.format (
        datetime.datetime.now ().isoformat (),
        period
    ))
    database = Database ()
    for method in METHODS:
        interpolation_process_command_line = method.command_line_arguments (
            resolution=INTERPOLATION_RESOLUTION)
        for a_data in data.DATA:
            if not a_data.route_planner_flag and not a_data.mobile_app_flag:
                continue
            number_rows = number_measurements_in_period (
                period=period,
                a_data=a_data,
                database=database)
            if number_rows > 0:
                fd_log.write ('{}:    {:10s} {:30s} {:10d}\n'.format (
                    datetime.datetime.now ().isoformat (),
                    method.description,
                    a_data.description_en,
                    number_rows
                ))
                interpolate_data (
                    database=database,
                    interpolation_command_line=interpolation_process_command_line,
                    method=method,
                    period=period,
                    a_data=a_data,
                    number_rows=number_rows
                )


def number_measurements_in_period (
        period: PeriodDaily,
        a_data: Data,
        database: Database,
):
    table_name = 'aggregation_' \
                 + INTERPOLATION_STATISTIC.sql_function + '_' \
                 + PeriodDaily.enum.sql_identifier + '_' \
                 + INTERPOLATION_RESOLUTION.sql_identifier + '_' \
                 + a_data.sql_identifier
    table_name = a_data.table_aggregation_name (
        s=INTERPOLATION_STATISTIC,
        p=PeriodDaily.enum,
        r=INTERPOLATION_RESOLUTION,
    )
    sql_statement = '''
    SELECT count (*)
    FROM {table_name}
    WHERE when_ >= %s AND when_ < %s
            '''.format (
        table_name=table_name)
    database.cursor.execute (sql_statement, (period.start, period.end))
    (number_rows,) = database.cursor.fetchone ()
    return number_rows


def interpolate_data (
        database: Database,
        interpolation_command_line: List[str],
        method: Method,
        period: PeriodDaily,
        a_data: Data,
        number_rows: int,
        ):
    # language=reStructuredText
    """
    Interpolate data in a given period using the given method.

    The data is saved in a table whose name is given by the interpolation method, period, and sensor data.

    We create a process that runs the interpolation algorithm.
    To communicate with this process, we use two threads.
    One pipes the sensor data from the database,
    and the other reads the interpolation output and saves it in the database

    :param number_rows: the number of rows in the data to be interpolated
    :param database: the database to commit the interpolated data
    :param interpolation_command_line: the interpolation process command line
    :param method: the name of the interpolation method
    :param period: the period to be interpolated
    :param a_data: the name of the sensor data to interpolate
    """
    interpolation_process = subprocess.Popen (
        interpolation_command_line,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True,
        shell=False,
    )
    send_data_thread = SendDataThread (
        cursor=database.cursor,
        interpolation_process=interpolation_process,
        period=period,
        the_data=a_data,
        number_rows=number_rows,
    )
    save_data_thread = SaveDataThread (
        cursor=database.cursor,
        interpolation_process=interpolation_process,
        method=method,
        period=period,
        the_data=a_data,
    )
    send_data_thread.start ()
    save_data_thread.start ()
    interpolation_process.wait ()
    send_data_thread.join ()
    save_data_thread.join ()
    database.connection.commit ()


with open ('/var/log/expolis/interpolate-data-day', 'a') as fd:
    fd.write ('{}: start\n'.format (datetime.datetime.now ().isoformat ()))
    try:
        main (fd)
    except Exception as e:
        fd.write ('{}: error {}\n'.format (
            datetime.datetime.now ().isoformat (),
            e,
        ))
    fd.write ('{}: end\n'.format (datetime.datetime.now ().isoformat ()))
