import subprocess
import threading
from typing import List, TextIO

import log


def run_command (
        command_line: List[str],
        fd_log: TextIO,
):
    """
    Function used by cron scripts to run a command and to capture its output and write it to the log file.
    :param command_line: the command line to run.
    :param fd_log: the file descriptor of the log file.
    """
    def consume_output ():
        log.log (fd_log, 'RUN_COMMAND')
        log.write (fd_log, ' '.join (command_line))
        has_output = False
        for line in process.stdout:
            if not has_output:
                has_output = True
                log.log (fd_log, 'OUTPUT_BEGIN')
            log.write (fd_log, line [:-1])
        if has_output:
            log.log (fd_log, 'OUTPUT_END')
        else:
            log.log (fd_log, 'NO_OUTPUT')
    process = subprocess.Popen (
        command_line,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
        text=True,
    )
    thread = threading.Thread (target=consume_output)
    process.stdin.close ()
    thread.start ()
    thread.join ()
    return_code = process.wait ()
    if return_code != 0:
        log.log (fd_log, 'RETURN_CODE {}'.format (return_code))
