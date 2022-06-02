"""
This module contains the interpolation periods.
"""

import period

from typing import Union
import datetime


class Period:
    """
    Base class of all interpolation periods.
    All objects of this class have two attributes, representing the start and end date of the period.
    The period goes from the starting date (inclusive) to the end date (exclusive).
    """
    sql_identifier = None
    enum = None

    def __init__ (
            self,
            when: datetime = None):
        """
        'Abstract' constructor.
        :param when: represents a date of the interpolation period.
          Used to compute the starting and end date of the period.
        """
        if when is None:
            self.when = datetime.datetime.today ()
        else:
            self.when = when
        self.start = None
        self.end = None

    def __str__ (self):
        return '{}-{}'.format (
            self.start,
            self.end
        )


class PeriodHourly (Period):
    """
    Hourly interpolation period.
    """
    sql_identifier = period.HOURLY.sql_identifier
    enum = period.HOURLY

    def __init__(
            self,
            when: Union[str, datetime.datetime] = None):
        """
        Create a hourly interpolation period.
        :param when: if not specified, uses the current time,
         otherwise it should be a string with the format `YYYY-MM-DD HH`, where
         YYYY is the year, MM is the month, DD is the day, and HH is the hour where
         the interpolation is going to be made.
        """
        Period.__init__ (self, __when__ (when, '%Y-%m-%d %H'))
        self.start = datetime.datetime (
            year=self.when.year,
            month=self.when.month,
            day=self.when.day,
            hour=self.when.hour
        )
        self.end = self.start + datetime.timedelta (hours=1)

    def next (self) -> Period:
        return PeriodHourly (self.end)


class PeriodDaily (Period):
    """
    Daily interpolation period.
    """
    sql_identifier = period.DAILY.sql_identifier  # type: str
    enum = period.DAILY  # type: period.Period

    def __init__ (
            self,
            when: Union[str, datetime.date, datetime.datetime] = None):
        """
        Create a daily interpolation period.
        :param when: if not specified, uses the current time,
         otherwise it should be a string with the format `YYYY-MM-DD`, where
         YYYY is the year, MM is the month and DD is the day
         where the interpolation is going to be made.
        """
        Period.__init__ (self, __when__ (when, '%Y-%m-%d'))
        self.start = datetime.datetime (
            year=self.when.year,
            month=self.when.month,
            day=self.when.day,
        )
        self.end = self.start + datetime.timedelta (days=1)

    def next (self) -> Period:
        return PeriodDaily (self.end)


def __when__ (
        when: Union[str, datetime.date, datetime.datetime],
        date_format: str
        ) -> datetime:
    if when is None:
        return None
    elif type (when) is str:
        return datetime.datetime.strptime (when, date_format)
    elif type (when) is datetime.datetime:
        return when


PERIODS = {
    'hourly': PeriodHourly,
    'daily': PeriodDaily,
}
