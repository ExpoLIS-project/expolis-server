# language=markdown
"""
This module provides the class `Period` that represents common characteristics of time periods.

Objects of this class are used to:

* generate SQL tables and functions that deal with data interpolation;
* insert data in SQL tables that contain interpolated data.
* generate SQL tables and functions that deal with data aggregation;
* insert data in SQL tables that contain aggregated data.

The variable `PERIODS` contains a list of the time periods that are used in the ExpoLIS project.
"""


class Period:
    """
    Represents generic characteristics of time periods.
    """
    def __init__ (
            self,
            sql_identifier,
            description,
            date_trunc: str,
            ):
        """
        Sole constructor.
        :type date_trunc: str
        :param sql_identifier: the identifier used in SQL tables and functions that deal with time periods.
        :param date_trunc: the value to be used in the first argument of the SQL date_trunc function.
        """
        self.sql_identifier = sql_identifier
        self.description = description
        self.date_trunc = date_trunc

    def __repr__(self):
        return self.description


HOURLY = Period (
    sql_identifier='hourly',
    description='hourly',
    date_trunc='hour',
)

DAILY = Period (
    sql_identifier='daily',
    description='daily',
    date_trunc='day',
)

PERIODS = [
    HOURLY,
    DAILY,
]
