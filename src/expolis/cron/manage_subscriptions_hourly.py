#!/usr/bin/env python3

import csv
import datetime
import os
import smtplib
import ssl
import tempfile

from psycopg2.extensions import cursor
from typing import Tuple, List

import data
from data import Data
from database import Database

EMAIL = 'expolis.iscte@gmail.com'

WEB_SERVER_IP = '95.94.88.125'

DATA_SET_FOLDER = '/var/www/html/dataset'
DATA_SET_EXPIRE = 3
DATA_SET_PREFIX = 'data-request_'


def main ():
    data.load_data ()
    email_server = connect_email_server ()
    now = datetime.datetime.now ()
    span_hour = datetime.timedelta (seconds=3600)
    last_hour = (
        datetime.datetime (now.year, now.month, now.day, now.hour, 0, 0, 0) - span_hour,
        datetime.datetime (now.year, now.month, now.day, now.hour, 0, 0, 0)
    )
    print ('from ' + last_hour [0].isoformat () + ' to ' + last_hour [1].isoformat ())
    sensor_data_db = Database ()
    subscription_db = Database ()
    sql_command = 'SELECT * FROM subscriptions'
    subscription_db.cursor.execute (sql_command)
    for subscription_row in subscription_db.cursor:
        if subscription_row [2] == 1:
            csv_filename, has_data = create_csv_file (sensor_data_db.cursor, subscription_row, last_hour)
            if has_data:
                send_email_data (email_server, subscription_row [0], subscription_row [1], last_hour, csv_filename)
            else:
                os.remove (csv_filename)


def connect_email_server () -> smtplib.SMTP_SSL:
    """
    Establish a connection to the SMTP server.
    :return:
    """
    with open ('/opt/expolis/etc/account-mail', 'r') as fd:
        password = fd.readline ()
    # Log in to server using secure context and send email
    context = ssl.create_default_context ()
    # noinspection SpellCheckingInspection
    result = smtplib.SMTP_SSL ('smtp.gmail.com', 465, context=context)
    result.login (EMAIL, password)
    return result


def create_csv_file (
        sensor_data_cursor: cursor,
        subscription_row,
        period: Tuple[datetime.datetime, datetime.datetime],
) -> Tuple[str, bool]:
    """
    Create a CSV file with data from the given period.

    The file is created in the temporary folder and is deleted after the current batch of data requests is processed.
    :param sensor_data_cursor: the connection to the sensor data database.
    :param subscription_row:
    :param period: tuple with starting and end date.
    :return: the filename of the CSV file and a boolean indicating if there is data.
    """
    subs = [
        d
        for d in data.DATA
        if d.subscribe_flag
    ]
    fields = [
        d
        for d, s in zip (subs, subscription_row [3:])
        if s
    ]  # type: List[Data]
    number_rows = 0
    with tempfile.NamedTemporaryFile (
            mode='w',
            prefix=DATA_SET_PREFIX,
            suffix='.csv',
            delete=False,
            dir=DATA_SET_FOLDER) as fd:
        writer = csv.writer (fd, dialect='excel')
        header = ['timestamp', 'node id', 'longitude', 'latitude', 'gps error']
        header.extend ([d.description_en for d in fields])
        writer.writerow (header)
        sensor_data_cursor.execute (sql_command_sensor_data (fields), (period [0], period [1]))
        for row in sensor_data_cursor:
            writer.writerow (row)
            number_rows += 1
        result = fd.name
        fd.delete = number_rows == 0
    return result, number_rows > 0


def sql_command_sensor_data (fields: List[Data]) -> str:
    """
    Return the SQL command to obtain sensor data.
    :return: the SQL command to obtain sensor data.
    """
    return '''
SELECT
    measurement_properties.when_,
    measurement_properties.nodeID,
    measurement_properties.longitude,
    measurement_properties.latitude,
    measurement_properties.gps_error,
    {fields}
FROM measurement_properties
    {tables}
WHERE
    measurement_properties.when_ >= %s AND measurement_properties.when_ < %s
ORDER BY when_
'''.format (
            fields=',\n    '.join ([
                'measurement_data_{}.value'.format (d.sql_identifier)
                for d in fields
            ]),
            tables='\n    '.join ([
                'INNER JOIN measurement_data_{sql_identifier} '
                'ON measurement_properties.ID = measurement_data_{sql_identifier}.mpID'.format (
                    sql_identifier=d.sql_identifier
                )
                for d in fields
            ]),
        )


def send_email_data (
        server: smtplib.SMTP_SSL,
        to_email: str,
        salt: str,
        period: Tuple[datetime.datetime, datetime.datetime],
        filename: str,
) -> None:
    """
    Send an email with the data requested by the given person.
    :param server: the mail server used to send the email.
    :param to_email: the person email
    :param period:
    :param salt:
    :param filename: the filename of the CSV
    """
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    message = MIMEMultipart ()
    message ['From'] = EMAIL
    message ['To'] = to_email
    message ['Subject'] = 'Expolis data'
    body = '''Sensor data from {} up to {} is available at this link:

http://{web_server_ip}/{}

This link is valid for {} days.

To unsubscribe:

http://{web_server_ip}/unsubscribe.php?id={}

The ExpoLIS project
'''.format (
        period[0].isoformat (),
        period[1].isoformat (),
        os.path.basename (filename),
        DATA_SET_EXPIRE,
        salt,
        web_server_ip=WEB_SERVER_IP,
    )
    message.attach (MIMEText (body, 'plain'))
    text = message.as_string ()
    server.sendmail (EMAIL, to_email, text)


if __name__ == '__main__':
    main ()
