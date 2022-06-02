"""
This module provides the class `Statistics` that represents the aggregation functions used in analysing the sensor data.

The variable `STATISTICS` contains a list of the instances of the above class.
"""

from typing import Callable


class Statistic:
    def __init__ (
            self,
            sql_function: str,
            sql_type: Callable[[str], str],
            java_identifier: str,
            java_enum: str,
            description: str):
        """
        Construct a new instance of this class.

        :param sql_function: the sql function that aggregates the data.
        :param sql_type: the sql type of the value returned by the sql function.
        :param java_identifier: the infix used in java identifiers that deal with this aggregation function.
        :param java_enum: the java enumeration that represents this aggregation function.
        :param description: a short description used in comments of source code  that deal with this aggregation
        function.
        """
        self.sql_function = sql_function
        self.sql_type = sql_type
        self.java_identifier = java_identifier
        self.java_enum = java_enum
        self.description = description

    def __str__ (self):
        return self.description


def __avg_type__ (s):
    if s == 'integer':
        return 'numeric'
    elif s == 'real':
        return 'double precision'
    else:
        raise NotImplementedError ('Unhandled type {}'.format (s))


def __avg_max_min__ (s):
    return s


AVG = Statistic (
    sql_function='avg',
    sql_type=__avg_type__,
    java_identifier='Average',
    java_enum='AVERAGE',
    description='average',
)
MAX = Statistic (
    sql_function='max',
    sql_type=__avg_max_min__,
    java_identifier='Maximum',
    java_enum='MAXIMUM',
    description='maximum',
)
MIN = Statistic (
    sql_function='min',
    sql_type=__avg_max_min__,
    java_identifier='Minimum',
    java_enum='MINIMUM',
    description='minimum'
)

STATISTICS = [
    AVG,
    MAX,
    MIN,
]
"""
The list with the aggregation functions used in analysing the sensor data.
"""
