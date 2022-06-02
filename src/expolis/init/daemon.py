import subprocess
from typing import List


def run_command (command_line: List[str]):
    """
    Create a daemon process with the given command line arguments.
    Return the process identification.
    :param command_line: the command line arguments.
    :return: pid of created process.
    """
    process = subprocess.Popen (
        command_line,
        shell=False,
    )
    return process.pid
