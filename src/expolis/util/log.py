import datetime
from typing import TextIO


def log (fd: TextIO, line: str):
    fd.write ('{}: {}\n'.format (
        datetime.datetime.now ().isoformat (),
        line
    ))


def write (fd: TextIO, line: str):
    fd.write ('{}\n'.format (
        line,
    ))
