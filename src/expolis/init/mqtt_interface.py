#!/usr/bin/python3

"""
This module takes care of receiving mqtt messages from sensor nodes.
"""
import datetime
import os
import os.path
import signal
import sys
import time
from typing import Optional, Any

import paho.mqtt.client
import psutil
from psycopg2 import IntegrityError
from paho.mqtt.client import Client, MQTTMessage

import data
import log
import missing_data
from database import Database


MQTT_INTERFACE_PID_FILE = '/tmp/expolis/mqtt-interface.pid'
MQTT_INTERFACE_LOG_FILE = '/var/log/expolis/mqtt-interface.log'

# noinspection SpellCheckingInspection
MQTT_BROKER_ADDRESS = 'mqtt.eclipseprojects.io'

mqtt_client = None  # type: Optional[Client]
"""
The mqtt client instance used to connect to the mqtt broker."""

mqtt_running = False
"""
Flag that indicates if the mqtt client is running.
"""

WAIT_CONNECTION_DATABASE = 10
"""
Time to wait before connecting to PostgreSQL database. Unit is seconds.
"""

WAIT_RETRIAL = 5
"""
Time to wait before retrying to connect to MQTT broker. Unit is seconds.
"""

CONNECTION_RESULT = {
    0: 'Connection successful',
    1: 'Connection refused - incorrect protocol version',
    2: 'Connection refused - invalid client identifier',
    3: 'Connection refused - server unavailable',
    4: 'Connection refused - bad username or password',
    5: 'Connection refused - not authorised',
}


class Message:
    """
    Represents the data sent by a sensor node through the mqtt broker.
    """

    def __init__ (self, message: MQTTMessage):
        elements = message.payload.decode ('utf-8').split (' ')
        self.node_id = int (elements[0])
        self.message_index = int (elements[1])
        format_timestamp = \
            '%Y-%m-%dT%H:%M:%S' if elements[3].find ('.') == -1 else \
            '%Y-%m-%dT%H:%M:%S.%f'
        self.when = datetime.datetime.strptime (
            elements[2] + 'T' + elements[3],
            format_timestamp
        )  # type: datetime.datetime
        self.timestamp = self.when.timestamp ()
        self.latitude = float (elements[4])
        self.longitude = float (elements[5])
        self.gps_error = float (elements[19])
        self.sensor_data = {}
        for d in data.DATA:
            self.sensor_data [d.sql_identifier] = (d.sql_type, elements [d.mqtt_message_index])
        missing_data.add_message_info (
            sensor_id=self.node_id,
            message_index=self.message_index,
            message_timestamp=self.timestamp
        )


def start ():
    data.load_data ()
    if os.path.exists (MQTT_INTERFACE_PID_FILE):
        print ('ExpoLIS MQTT interface process is already running!')
        sys.exit (1)
    print ('Launching ExpoLIS MQTT interface process...')
    fork_result = os.fork ()
    if fork_result == 0:
        global mqtt_client
        mqtt_client = paho.mqtt.client.Client (
            client_id='ExpoLIS_mqtt_interface',
            clean_session=False,
        )
        mqtt_client.on_message = __on_message
        mqtt_client.on_connect = __on_connect
        mqtt_client.on_disconnect = __on_disconnect
        connected = False
        trial = 0
        while trial < 5 and not connected:
            try:
                mqtt_client.connect (MQTT_BROKER_ADDRESS)
                connected = True
            except Exception as e:
                trial += 1
                log_message ('Connection failed with: {}'.format (e))
                log_message ('Retrying in {} seconds'.format (WAIT_RETRIAL))
                time.sleep (WAIT_RETRIAL)
        if connected:
            missing_data.start_request_missing_data_timer (mqtt_client)
            mqtt_client.loop_start ()
            signal.signal (signal.SIGTERM, __terminate_mqtt_client)
        else:
            if os.path.exists (MQTT_INTERFACE_PID_FILE):
                log_message ('Removing file with PID of ExpoLIS MQTT interface process')
                os.unlink (MQTT_INTERFACE_PID_FILE)
    else:
        if not os.path.exists (os.path.dirname (MQTT_INTERFACE_PID_FILE)):
            os.makedirs (os.path.dirname (MQTT_INTERFACE_PID_FILE))
        with open (MQTT_INTERFACE_PID_FILE, 'w') as fd:
            fd.write ('{}\n'.format (fork_result))
        print ('PID of ExpoLIS MQTT interface process is {}'.format (fork_result))


def stop ():
    if not os.path.exists (MQTT_INTERFACE_PID_FILE):
        print ('ExpoLIS MQTT interface process is not running!')
        sys.exit (1)
    with open (MQTT_INTERFACE_PID_FILE, 'r') as fd:
        pid = int (fd.readline ())
        os.kill (pid, signal.SIGTERM)
        print ('Terminated process {}.'.format (pid))
    os.remove (MQTT_INTERFACE_PID_FILE)


def status ():
    if os.path.exists (MQTT_INTERFACE_PID_FILE):
        with open (MQTT_INTERFACE_PID_FILE, 'r') as fd:
            pid = int (fd.readline ())
            try:
                process = psutil.Process (pid=pid)
                command_line = process.cmdline ()
                if len (command_line) == 3 and \
                        command_line [0] == 'python3' and \
                        command_line [1] == '/opt/expolis/bin/mqtt_interface.py' and \
                        command_line [2] == 'start':
                    print ('PID of MQTT interface process is {}.'.format (pid))
                else:
                    print ('There is a process running whose PID matches the recorded MQTT interface process, '
                           'but its command line is not conformant:\n{}'.format (
                                ' '.join (command_line)
                    ))
            except psutil.NoSuchProcess:
                print ('There is no MQTT interface process running with the recorded PID!')
                print ('You should delete the file {}'.format (MQTT_INTERFACE_PID_FILE))
    else:
        print ('MQTT interface process is not running.')


def __terminate_mqtt_client (_signal_number, _stack_frame):
    global mqtt_client
    if mqtt_client is not None:
        log_message ('Received SIGTERM')
        missing_data.stop_requesting_data ()
        mqtt_client.loop_stop ()
        mqtt_client = None


def __on_connect (
        client: Client,
        _user_data,
        _flags,
        rc: int,
):
    """
    Callback that subscribes to the sensor node data messages.
    For every row in sql table node_sensors we subscribe to topic expolis_project/sensor_nodes/sn_ID where ID is the
    sql column ID.
    :param client:
    :param _user_data: not used.
    :param _flags: not used.
    :param rc: connection result.
    """
    log_message (CONNECTION_RESULT [rc])
    if rc == 0:
        log_message ('Waiting {}s before establishing connection to database...'.format (WAIT_CONNECTION_DATABASE))
        time.sleep (WAIT_CONNECTION_DATABASE)
        db = Database ()
        log_message ('Connected to database')
        sql_statement = 'SELECT mqtt_topic_number FROM node_sensors'
        db.cursor.execute (sql_statement)
        for row in db.cursor:
            topic = __mqtt_sensor_node_data_topic (row[0])
            log_message ('Subscribing to topic {}'.format (row[0]))
            client.subscribe (topic, qos=2)


def __mqtt_sensor_node_data_topic (
        mqtt_topic_number: int,
) -> str:
    """
    Returns the mqtt topic to receive data from the given sensor node id.
    :param mqtt_topic_number: the sensor node id.
    :return: a string representing the mqtt topic.
    """
    return 'expolis_project/sensor_nodes/sn_{}'.format (mqtt_topic_number)


def __on_message (
        _client: Client,
        _user_data: Any,
        message: MQTTMessage,
):
    try:
        msg = Message (message)
        db = Database ()
        sql_command = '''
        SELECT * FROM insert_measurements (
            CAST (%s AS INTEGER),
            CAST (%s AS TIMESTAMP),
            CAST (%s AS REAL),
            CAST (%s AS DOUBLE PRECISION),
            CAST (%s AS DOUBLE PRECISION)'''
        sql_args = [
            msg.node_id,
            msg.when.strftime ('%Y-%m-%d %H:%M:%S.%f'),
            msg.gps_error,
            msg.longitude,
            msg.latitude,
        ]
        for sql_identifier in msg.sensor_data:
            sql_type, value = msg.sensor_data [sql_identifier]
            sql_command += ', {} => CAST (%s AS {})'.format (sql_identifier, sql_type)
            sql_args += [value]
        sql_command += ')'
        try:
            db.cursor.execute (sql_command, sql_args)
        except IntegrityError:
            log_message ('Data of message id {} already exists in database'.format (msg.message_index))
    except IndexError:
        log_message ('Contents of MQTT message changed:\n{}'.format (str (message)))
        return


def __on_disconnect (client, userdata, rc):
    if rc != 0:
        log_message ('Unexpected disconnection. {}'.format (paho.mqtt.client.connack_string (rc)))


def log_message (msg: str):
    with open (MQTT_INTERFACE_LOG_FILE, 'a') as fd:
        log.log (fd, msg)


if __name__ == '__main__':
    if len (sys.argv) == 2:
        if sys.argv [1] == 'start':
            start ()
        elif sys.argv [1] == 'stop':
            stop ()
        elif sys.argv [1] == 'status':
            status ()
        else:
            print ('Unknown command {}\nUsage:\n{} start|stop|status'.format (
                sys.argv [1],
                sys.argv [0]))
    else:
        print ('{} start|stop|status'.format (sys.argv [0]))
