#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import os
import string
import subprocess
import time
from typing import Any, List, Optional

import paho.mqtt.client
import psutil

import data
import database
import mqtt_interface


data.load_data ()

ADD_SENSOR_NODES = '1'
RESET_SENSOR_INTERVALS = '2'
START_STOP_MQTT_INTERFACE_SERVICE = '3'
POSTGRESQL_SHELL = '4'
DATA_OVERVIEW = '5'
SENSOR_OVERVIEW = '6'
SHOW_STORED_PROCEDURES = '7'
EXIT = '0'


def main ():
    enable_curses ()
    check_mqtt_interface_init_service ()
    start_mqtt_client ()
    go = True
    while go:
        option = menu_option ()
        if option == ADD_SENSOR_NODES:
            create_sensor_nodes ()
        elif option == RESET_SENSOR_INTERVALS:
            reset_data_intervals ()
        elif option == START_STOP_MQTT_INTERFACE_SERVICE:
            start_stop_mqtt_interface_service ()
        elif option == POSTGRESQL_SHELL:
            start_postgresql_shell ()
        elif option == DATA_OVERVIEW:
            data_overview ()
        elif option == SENSOR_OVERVIEW:
            sensor_data_overview ()
        elif option == SHOW_STORED_PROCEDURES:
            show_stored_procedures ()
        elif option == EXIT:
            the_end ()
            go = False
    print ('Good bye')


# region menu options
def create_sensor_nodes ():
    def read_int (prompt):
        while True:
            try:
                return int (input (prompt))
            except ValueError:
                print ('Please enter a number!')

    def read_input (prompt, default):
        result = input ('{} [{}]? '.format (prompt, default))
        return default if result == '' else result
    disable_curses ()
    number_nodes = read_int ('How many sensor nodes? ')
    db = database.Database ()
    sql_statement = 'SELECT COUNT (*) FROM node_sensors'
    db.cursor.execute (sql_statement)
    adjust = db.cursor.fetchone () [0] + 1
    for index_node in range (adjust, number_nodes + adjust):
        index_item = index_node - adjust + 1
        db.cursor.callproc (
            'insert_bus',
            {
                'description': read_input (
                    'Description of bus #{}'.format (index_item),
                    'virtual bus #{}'.format (index_node)
                ),
            }
        )
        bus_id = db.cursor.fetchone ()[0]
        db.cursor.callproc (
            'insert_node_sensors',
            {
                'bus_id': bus_id,
                'serial_description': read_input (
                    'Serial description of sensor #{}'.format (index_item),
                    'virtual sensor node #{}'.format (index_node)
                ),
                'mqtt_topic_number': read_int (
                    'MQTT topic of sensor #{}? '.format (index_item)
                ),
            }
        )
    new_log ('Inserted {} virtual buses and sensor nodes.'.format (number_nodes))
    enable_curses ()


def data_overview ():
    db = database.Database ()
    sql_statement = 'SELECT COUNT (*) FROM node_sensors'
    db.cursor.execute (sql_statement)
    number_node_sensors = db.cursor.fetchone ()[0]
    sql_statement = 'SELECT COUNT (*) FROM measurement_properties'
    db.cursor.execute (sql_statement)
    number_measurements = db.cursor.fetchone ()[0]
    new_log ('There are {} node sensors.'.format (number_node_sensors))
    new_log ('There are {} measurements.'.format (number_measurements))
    if number_measurements > 0:
        sql_statement = 'SELECT MIN (when_), MAX (when_) FROM measurement_properties'
        db.cursor.execute (sql_statement)
        row = db.cursor.fetchone ()
        last_measurement = row[1]
        first_measurement = row[0]
        new_log (
            'The first measurement was in {} and the last measurement was in {}.'.format (
                first_measurement,
                last_measurement,
            )
        )


def reset_data_intervals ():
    disable_curses ()
    command = [
        '/etc/init.d/expolis_mqtt_interface',
        'stop',
    ]
    process = subprocess.Popen (command)
    process.wait ()
    if process.returncode != 0:
        new_log ('A problem occurred while stopping the MQTT interface service')
    if os.path.exists ('/var/lib/expolis/message_intervals'):
        os.remove ('/var/lib/expolis/message_intervals')
    command = [
        '/etc/init.d/expolis_mqtt_interface',
        'start',
    ]
    process = subprocess.Popen (command)
    process.wait ()
    if process.returncode != 0:
        new_log ('A problem occurred while starting the MQTT interface service')
    new_log ('File with received MQTT message ids was reset')
    time.sleep (3)
    enable_curses ()


def start_stop_mqtt_interface_service ():
    disable_curses ()
    if os.path.exists (mqtt_interface.MQTT_INTERFACE_PID_FILE):
        command = [
            '/etc/init.d/expolis_mqtt_interface',
            'stop',
        ]
        process = subprocess.Popen (command)
        process.wait ()
        if process.returncode != 0:
            new_log ('A problem occurred while stopping the MQTT interface service')
    else:
        command = [
            '/etc/init.d/expolis_mqtt_interface',
            'start',
        ]
        process = subprocess.Popen (command)
        process.wait ()
        if process.returncode != 0:
            new_log ('A problem occurred while starting the MQTT interface service')
    check_mqtt_interface_init_service ()
    time.sleep (3)
    enable_curses ()


def start_postgresql_shell ():
    disable_curses ()
    with open ('/opt/expolis/etc/config-database', 'r') as fd:
        _database = fd.readline () [:-1]
        _username = fd.readline () [:-1]
    # noinspection SpellCheckingInspection
    command = [
        '/usr/bin/psql',
        '--dbname', _database,
        '--username', _username,
    ]
    process = subprocess.Popen (command)
    process.wait ()
    enable_curses ()


def sensor_data_overview ():
    disable_curses ()
    print ('''\
   name   | mqtt | type | mobile | planner | subscribe | profile
----------+------+------+--------+---------+-----------+---------
sensor id |    0 |      |        |         |     V     |
timestamp | 2, 3 |      |    V   |         |     V     |
longitude |    4 |      |    V   |         |     V     |
latitude  |    5 |      |    V   |         |     V     |
gps error |   19 |      |    V   |         |     V     |
----------+------+------+--------+---------+-----------+---------''')
    for a_data in data.DATA:
        print ('{: <10s}|{: >6d}| {: >4s} |    {}   |    {}    |     {}     | {}'.format (
            a_data.sql_identifier [:10],
            a_data.mqtt_message_index,
            a_data.sql_type,
            'Y' if a_data.mobile_app_flag else '.',
            'Y' if a_data.route_planner_flag else '.',
            'Y' if a_data.subscribe_flag else '.',
            '{} x + {}'.format (a_data.pollution_profile_m, a_data.pollution_profile_b)
            if a_data.route_planner_flag else ''
        ))
    input ('Press ENTER to return')
    enable_curses ()


def show_stored_procedures ():
    disable_curses ()
    with open ('/opt/expolis/etc/config-database', 'r') as fd:
        _database = fd.readline () [:-1]
        _username = fd.readline () [:-1]
    # noinspection SpellCheckingInspection
    command = [
        '/usr/bin/psql',
        '--dbname', _database,
        '--username', _username,
    ]
    postgres_process = subprocess.Popen (
        command,
        stdin=subprocess.PIPE,
        universal_newlines=True,
    )
    # noinspection SpellCheckingInspection
    postgres_process.communicate ('''
\\o /tmp/expolis/stored-procedures.txt
SELECT pg_proc.oid, pg_proc.proname, pg_proc.proargtypes, pg_proc.proargnames, \
pg_proc.prorettype, pg_type.typname, pg_proc.prosrc
    FROM pg_proc
        INNER JOIN pg_roles ON pg_proc.proowner = pg_roles.oid
        INNER JOIN pg_type ON pg_proc.prorettype = pg_type.oid
    WHERE
        pg_roles.rolname = 'expolis_admin'
    ORDER BY pg_proc.proname
    ;
''')
    postgres_process.wait ()
    subprocess.Popen ([
        '/usr/bin/less',
        '-S',
        '/tmp/expolis/stored-procedures.txt',
    ]).wait ()
    enable_curses ()


def the_end ():
    mqtt_client.disconnect ()
    disable_curses ()
    print ()
# endregion


# region MQTT
mqtt_client = None  # type: Optional[paho.mqtt.client.Client]
"""
The mqtt client instance used to connect to the mqtt broker."""

CONNECTION_RESULT = {
    0: 'Connection successful',
    1: 'Connection refused - incorrect protocol version',
    2: 'Connection refused - invalid client identifier',
    3: 'Connection refused - server unavailable',
    4: 'Connection refused - bad username or password',
    5: 'Connection refused - not authorised',
}

is_mqtt_interface_service_running = False  # type: bool


class Message:
    """
    Represents the data sent by a sensor node through the mqtt broker.
    """

    def __init__ (self, message: paho.mqtt.client.MQTTMessage):
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
            self.sensor_data [d.sql_identifier] = float (elements [d.mqtt_message_index])


def check_mqtt_interface_init_service ():
    if os.path.exists (mqtt_interface.MQTT_INTERFACE_PID_FILE):
        with open (mqtt_interface.MQTT_INTERFACE_PID_FILE, 'r') as fd:
            pid = int (fd.readline ())
        try:
            process = psutil.Process (pid=pid)
            command_line = process.cmdline ()
            if len (command_line) == 3 and \
                    command_line [0] == 'python3' and \
                    command_line [1] == '/opt/expolis/bin/mqtt_interface.py' and \
                    command_line [2] == 'start':
                set_mqtt_status ('running')
            else:
                set_mqtt_status ('problem WCL')
        except psutil.NoSuchProcess:
            set_mqtt_status ('problem NSP')
    else:
        set_mqtt_status ('stopped')


def start_mqtt_client ():
    global mqtt_client
    mqtt_client = paho.mqtt.client.Client (
        client_id='ExpoLIS_control_panel',
        clean_session=True,
    )
    mqtt_client.on_message = __on_message
    mqtt_client.on_connect = __on_connect
    mqtt_client.connect (mqtt_interface.MQTT_BROKER_ADDRESS)
    mqtt_client.loop_start ()


def __on_connect (
        client: paho.mqtt.client.Client,
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
    new_log (CONNECTION_RESULT [rc])
    if rc == 0:
        db = database.Database ()
        sql_statement = 'SELECT mqtt_topic_number FROM node_sensors'
        db.cursor.execute (sql_statement)
        has_node_sensors = False
        for row in db.cursor:
            topic = __mqtt_sensor_node_data_topic (row[0])
            client.subscribe (topic, qos=2)
            new_log ('Subscribed to MQTT topic {}'.format (topic))
            has_node_sensors = True
        if not has_node_sensors:
            new_log ('There are no node sensors information in the database')


def __mqtt_sensor_node_data_topic (
        sensor_node_id: int,
) -> str:
    """
    Returns the mqtt topic to receive data from the given sensor node id.
    :param sensor_node_id: the sensor node id.
    :return: a string representing the mqtt topic.
    """
    return 'expolis_project/sensor_nodes/sn_{}'.format (sensor_node_id)


def __on_message (
        _client: paho.mqtt.client.Client,
        _user_data: Any,
        message: paho.mqtt.client.MQTTMessage,
):
    try:
        msg = Message (message)
        new_mqtt_message (msg)
    except IndexError:
        new_log ('Contents of MQTT message changed: {}'.format (str (message)))

# endregion


# region curses
__OPTIONS = [
    ADD_SENSOR_NODES,
    RESET_SENSOR_INTERVALS,
    START_STOP_MQTT_INTERFACE_SERVICE,
    POSTGRESQL_SHELL,
    DATA_OVERVIEW,
    SENSOR_OVERVIEW,
    SHOW_STORED_PROCEDURES,
    EXIT,
]

__DEFAULT_SENSOR_DATA_MQTT_MESSAGE_FIELDS = [
    'sensor id  ',
    'message    ',
    'time       ',
    '    stamp  ',
    'longitude  ',
    'latitude   ',
    'gps error  ',
]

# noinspection PyProtectedMember
screen = None  # type: Optional[curses.window]

curses_enabled = False

menu_lines = 0  # type: int
"""
How many lines the menu takes
"""

__line_mqtt_messages = 2  # type: int

__line_status = __line_mqtt_messages + len (__DEFAULT_SENSOR_DATA_MQTT_MESSAGE_FIELDS) + len (data.DATA)  # type: int

__line_log_messages = __line_status + 2  # type: int

__max_columns = 0  # type: int

mqtt_messages = []  # type: List[Message]
mqtt_status = 'stopped'  # type: str

log_messages = []  # type: List[str]


def enable_curses ():
    global screen, curses_enabled, __max_columns
    if screen is None:
        screen = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    screen.leaveok (False)
    draw_screen ()
    __max_columns = max (__max_columns, os.get_terminal_size ().columns)
    curses_enabled = True


def disable_curses ():
    global curses_enabled
    screen.leaveok (True)
    curses.nocbreak ()
    curses.echo ()
    curses.endwin ()
    curses_enabled = False


def draw_screen ():
    screen.clear ()
    draw_menu ()
    draw_sensor_data_mqtt_message_table ()
    draw_sensor_data_mqtt_messages ()
    draw_mqtt_status ()
    draw_log ()
    __refresh ()


def draw_menu ():
    global menu_lines
    labels = [
        ' {} - add sensor nodes'.format (ADD_SENSOR_NODES),
        ' {} - reset sensor intervals'.format (RESET_SENSOR_INTERVALS),
        ' {} - {} mqtt interface service'.format (
            START_STOP_MQTT_INTERFACE_SERVICE,
            'stop' if mqtt_status == 'running' else
            'start' if mqtt_status == 'stopped' else
            '?!*',
        ),
        ' {} - open postgres shell'.format (POSTGRESQL_SHELL),
        ' {} - data overview'.format (DATA_OVERVIEW),
        ' {} - sensor overview'.format (SENSOR_OVERVIEW),
        ' {} - show stored procedures'.format (SHOW_STORED_PROCEDURES),
        ' {} - exit'.format (EXIT)
    ]
    y = 0
    x = 0
    last_x = os.get_terminal_size ().columns
    for an_option in labels:
        if x + len (an_option) + 2 >= last_x:
            screen.clrtoeol ()
            x = 0
            y = y + 1
        elif x > 0:
            _screen_add_str (y, x, ' |')
            x = x + 2
        _screen_add_str (y, x, an_option)
        x = x + len (an_option)
    screen.clrtoeol ()
    screen.move (y + 1, 0)
    screen.clrtoeol ()
    menu_lines = y + 2
    global __line_log_messages, __line_mqtt_messages, __line_status
    __line_mqtt_messages = menu_lines + 2
    __line_status = __line_mqtt_messages + len (__DEFAULT_SENSOR_DATA_MQTT_MESSAGE_FIELDS) + len (data.DATA)
    __line_log_messages = __line_status + 2


def menu_option () -> str:
    while True:
        result = screen.getch ()
        if curses.ascii.unctrl (result) in __OPTIONS:
            return curses.ascii.unctrl (result)
        elif result == curses.KEY_RESIZE:
            draw_screen ()
            global __max_columns
            __max_columns = max (__max_columns, os.get_terminal_size ().columns)
            __refresh ()


def set_mqtt_status (s: str):
    global mqtt_status
    mqtt_status = s
    if curses_enabled:
        draw_mqtt_status ()
        __refresh ()


def draw_mqtt_status ():
    _screen_add_str (__line_status, 0, 'MQTT status: {}'.format (mqtt_status))
    screen.clrtoeol ()


def new_mqtt_message (msg):
    global mqtt_messages
    mqtt_messages.append (msg)
    if len (mqtt_messages) * 11 + 12 >= __max_columns:
        mqtt_messages = mqtt_messages [1:]
    if curses_enabled:
        draw_sensor_data_mqtt_messages ()
        __refresh ()


def draw_sensor_data_mqtt_message_table ():
    y = __line_mqtt_messages
    for field in __DEFAULT_SENSOR_DATA_MQTT_MESSAGE_FIELDS:
        _screen_add_str (y, 0, field)
        y = y + 1
    for a_data in data.DATA:
        _screen_add_str (y, 0, a_data.sql_identifier)
        y += 1


def draw_sensor_data_mqtt_messages ():
    last_x = os.get_terminal_size ().columns
    x = 12
    for message in mqtt_messages:
        _screen_add_str (__line_mqtt_messages, x, '{: >6d}'.format (message.node_id))
        _screen_add_str (__line_mqtt_messages + 1, x, '{: >6d}'.format (message.message_index))
        _screen_add_str (__line_mqtt_messages + 2, x, message.when.strftime ('%Y-%m-%d'))
        _screen_add_str (__line_mqtt_messages + 3, x, message.when.strftime ('%H:%M:%S'))
        _screen_add_str (__line_mqtt_messages + 4, x, __sensor_data_number (message.longitude))
        _screen_add_str (__line_mqtt_messages + 5, x, __sensor_data_number (message.latitude))
        _screen_add_str (__line_mqtt_messages + 6, x, __sensor_data_number (message.gps_error))
        y = 7
        for a_data in data.DATA:
            _screen_add_str (
                __line_mqtt_messages + y,
                x,
                __sensor_data_number (message.sensor_data [a_data.sql_identifier]))
            y += 1
        x = x + 11
        if x >= last_x:
            break


def __sensor_data_number (field: float) -> str:
    return ('{: >10.2f}' if field < 10 else '{: >10.1f}').format (field)


def new_log (s):
    global log_messages
    last_y = os.get_terminal_size ().lines - 1
    log_messages.append (s)
    diff = len (log_messages) - (last_y - __line_log_messages + 1)
    if diff > 0:
        log_messages = log_messages [diff:]
    if curses_enabled:
        draw_log ()
        __refresh ()


def draw_log ():
    last_x = os.get_terminal_size ().columns
    y = min (os.get_terminal_size ().lines - 1, __line_log_messages + len (log_messages) - 1)
    i = -1
    while y >= __line_log_messages:
        if len (log_messages [i]) >= last_x:
            s = '{}...'.format (log_messages [i][:last_x - 3 - (1 if y == os.get_terminal_size ().lines - 1 else 0)])
        else:
            s = log_messages [i]
        _screen_add_str (y, 0, s)
        if len (log_messages [i]) < last_x:
            screen.clrtoeol ()
        y -= 1
        i -= 1


def ask_number_nodes () -> int:
    _screen_add_str (menu_lines, 0, 'How many sensor nodes? ')
    x = 23
    go = True
    result = ''
    while go:
        an_int = screen.getch ()
        a_char = curses.ascii.unctrl (an_int)
        if a_char in string.digits:
            result += a_char
            _screen_add_str (menu_lines, x, a_char)
            x += 1
        elif an_int == curses.KEY_BACKSPACE and len (result) > 0:
            result = result [:-1]
            x += -1
            _screen_add_str (menu_lines, x, ' ')
        else:
            _screen_add_str (menu_lines + x, x, str (an_int))
            _screen_add_str (menu_lines + x + 1, x, '[' + result + ']')

            if (an_int == curses.KEY_ENTER or an_int == 10) and len (result) > 0:
                return int (result)


def __ask_int (prompt: str, default: Optional[int] = None) -> int:
    prompt += '? '
    if default is not None:
        prompt += '[{}] '.format (default)
    _screen_add_str (menu_lines, 0, prompt)
    x = len (prompt)
    result = ''
    while True:
        an_int = screen.getch ()
        a_char = curses.ascii.unctrl (an_int)
        if a_char in string.digits:
            result += a_char
            _screen_add_str (menu_lines, x, a_char)
            x += 1
        elif an_int == curses.KEY_BACKSPACE and len (result) > 0:
            result = result [:-1]
            x += -1
            _screen_add_str (menu_lines, x, ' ')
        else:
            if an_int == curses.KEY_ENTER or an_int == 10:
                if len (result) > 0:
                    return int (result)
                elif len (result) == 0 and default is not None:
                    return default


def __ask_str (prompt: str, default: Optional[str] = None) -> str:
    prompt += '? '
    if default is not None:
        prompt += '[{}] '.format (default)
    _screen_add_str (menu_lines, 0, prompt)
    x = len (prompt)
    result = ''
    while True:
        an_int = screen.getch ()
        a_char = curses.ascii.unctrl (an_int)
        if len (a_char) == 1:
            result += a_char
            _screen_add_str (menu_lines, x, a_char)
            x += 1
        elif an_int == curses.KEY_BACKSPACE and len (result) > 0:
            result = result [:-1]
            x += -1
            _screen_add_str (menu_lines, x, ' ')
        else:
            if an_int == curses.KEY_ENTER or an_int == 10:
                if len (result) > 0:
                    return result
                elif len (result) == 0 and default is not None:
                    return default


def __refresh ():
    screen.move (menu_lines, 0)
    screen.refresh ()


def _screen_add_str (x: int, y: int, s: str):
    # noinspection PyArgumentList
    screen.addstr (x, y, s)
# endregion


if __name__ == '__main__':
    main ()
