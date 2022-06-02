#!/usr/bin/python3

import os.path
import posix_ipc
import signal
import sys
import yaml

import psutil

import daemon


OSRM_PID_FILE = '/tmp/expolis/osrm.pid'


def start ():
    if os.path.exists (OSRM_PID_FILE):
        print ('ExpoLIS Open Service Routing Machine processes are already running!')
        sys.exit (1)
    with open ('/opt/expolis/etc/config-osrm', 'r') as fd:
        config = yaml.safe_load (fd)
    if not os.path.exists (os.path.join ('/dev/shm', 'sem.' + config ['mutex'][1:])):
        posix_ipc.Semaphore (
            name=config ['mutex'],
            flags=posix_ipc.O_EXCL | posix_ipc.O_CREX,
            initial_value=1,
        )
        print ('Created ExpoLIS Open Service Routing Machine mutex.')
    else:
        print ('ExpoLIS Open Service Routing Machine mutex already exists.')
    list_pids = []
    for a_routing in config ['routing']:
        osrm_file_path = os.path.join (a_routing ['folder'], os.path.basename (config ['map_path']) [:-7] + 'osrm')
        print (osrm_file_path)
        pid = daemon.run_command (
            command_line=[
                '/usr/local/bin/osrm-routed',
                osrm_file_path,
                '--algorithm', 'mld',
                '--port', str (a_routing ['port']),
            ]
        )
        list_pids.append (str (pid))
    if not os.path.exists (os.path.dirname (OSRM_PID_FILE)):
        os.makedirs (os.path.dirname (OSRM_PID_FILE))
    with open (OSRM_PID_FILE, 'w') as fd:
        fd.write ('\n'.join (list_pids))


def stop ():
    if not os.path.exists (OSRM_PID_FILE):
        print ('ExpoLIS Open Service Routing Machine processes are not running!')
        sys.exit (1)
    with open (OSRM_PID_FILE, 'r') as fd:
        for line in fd:
            print ('Terminating process {}...'.format (line))
            os.kill (int (line), signal.SIGTERM)
    os.remove (OSRM_PID_FILE)


def status ():
    if os.path.exists (OSRM_PID_FILE):
        with open ('/opt/expolis/etc/config-osrm', 'r') as fd:
            config = yaml.safe_load (fd)
        print ('PIDs of ExpoLIS Open Service Routing Machine processes:')
        with open (OSRM_PID_FILE, 'r') as fd:
            for line in fd:
                pid = int (line)
                try:
                    process = psutil.Process (pid)
                    command_line = process.cmdline ()
                    match = False
                    if len (command_line) == 6 and \
                            command_line [0] == '/usr/local/bin/osrm-routed' and \
                            command_line [2] == '--algorithm' and command_line [3] == 'mld' and \
                            command_line [4] == '--port':
                        for index, a_routing in enumerate (config ['routing']):
                            osrm_file_path = os.path.join (
                                a_routing ['folder'],
                                os.path.basename (config ['map_path']) [:-7] + 'osrm')
                            if command_line [1] == osrm_file_path and command_line [5] == str (a_routing ['port']):
                                match = True
                                del config ['routing'][index:(index+1)]
                                break
                    if match:
                        print (pid)
                    else:
                        print ('There is a process running with a recorded PID, {}, but its command line is not '
                               'conformant!'.format (pid))
                except psutil.NoSuchProcess:
                    print ('There is no process running with a recorded PID, {}.'.format (pid))
    else:
        print ('ExpoLIS Open Service Routing Machine processes are not running.')


if len (sys.argv) == 2:
    if sys.argv [1] == 'start':
        start()
    elif sys.argv [1] == 'stop':
        stop()
    elif sys.argv [1] == 'status':
        status()
    else:
        print ('Unknown command {}\nUsage:\n{} start|stop|status'.format (
            sys.argv [1],
            sys.argv [0]))
else:
    print ('{} start|stop|status'.format (sys.argv [0]))
