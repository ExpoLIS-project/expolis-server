# language=markdown
"""
This module provides the class `Data` to represent data collected by a sensor.

Objects of this class are used by the init scripts:

* insert sensor data in the database.

Objects of this class are used by the cron scripts to:

* aggregate, interpolate daily and hourly data;
* handle data subscriptions;
* update route planner data.

Objects of this class are used by the database scripts to generate:

* the SQL tables that store values;
* the SQL functions to obtain graph data.

The variable `DATA` contains a list of the sensor data that are used in the
scripts of the ExpoLIS server.
"""

from typing import List, Optional

import yaml

import interpolation_method
import period
import resolution
import aggregation


class Data:
    """
    The class that represents data collected by a sensor.

    ____

    Attributes
        * sql_identifier - name used in the database to represent this sensor data.
        * description_en - a human-readable description of this sensor data.
        * pollution_profile_m - constant used when computing the weight of this sensor data in the pollution image.
        * pollution_profile_b - constant used when computing the weight of this sensor data in the pollution image.
    """

    def __init__ (
            self,
            sql_identifier: str,
            description_en: str,
            description_pt: str,
            sql_type: str,
            mqtt_message_index: int,
            mobile_app_flag: bool,
            route_planner_flag: bool,
            subscribe_flag: bool,
            pollution_profile_m: Optional[float] = None,
            pollution_profile_b: Optional[float] = None,
    ):
        """
        Creates a new instance of a sensor data.

        :param description_en: a short description of this sensor data that is used in comments.
        :param description_pt: a short description of this sensor data that is used in comments.
        :param sql_identifier: the suffix of the SQL table name where readings of this data are stored.
        :param sql_type: the SQL type used to store this data.
        """
        assert (route_planner_flag and pollution_profile_m is not None and pollution_profile_b is not None) or \
               (not route_planner_flag and pollution_profile_m is None and pollution_profile_b is None), \
               "if sensor data is to be used in the route planner, pollution profile constants must be specified"
        self.sql_identifier = sql_identifier
        self.description_en = description_en
        self.description_pt = description_pt
        self.sql_type = sql_type
        self.mqtt_message_index = mqtt_message_index
        self.mobile_app_flag = mobile_app_flag
        self.route_planner_flag = route_planner_flag
        self.subscribe_flag = subscribe_flag
        if pollution_profile_b is not None and pollution_profile_b is not None:
            self.pollution_profile_m = pollution_profile_m
            self.pollution_profile_b = pollution_profile_b

    def java_identifier (self) -> str:
        return self.sql_identifier.capitalize ()

    def java_enum (self) -> str:
        return self.sql_identifier.upper()

    def table_measurement_name (self) -> str:
        return 'measurement_data_{sql_identifier}'.format (
            sql_identifier=self.sql_identifier
        )

    def table_aggregation_name (
            self,
            s: aggregation.Statistic,
            p: period.Period,
            r: resolution.Resolution,
    ):
        return 'aggregation_{s}_{p}_{r}_{d}'.format (
            s=s.sql_function,
            p=p.sql_identifier,
            r=r.sql_identifier,
            d=self.sql_identifier,
        )

    def table_interpolation_name (
            self,
            m: interpolation_method.Method,
            p: period.Period,
    ) -> str:
        return 'interpolation_{method_sql_identifier}_{period_sql_identifier}_{data_sql_identifier}'.format (
            method_sql_identifier=m.sql_identifier,
            period_sql_identifier=p.sql_identifier,
            data_sql_identifier=self.sql_identifier,
        )

    def to_dict (self):
        result = {
            'sql_identifier': self.sql_identifier,
            'description_en': self.description_en,
            'description_pt': self.description_pt,
            'sql_type': self.sql_type,
            'mqtt_message_index': self.mqtt_message_index,
            'pollution_profile_b': self.pollution_profile_b if self.route_planner_flag else None,
            'pollution_profile_m': self.pollution_profile_m if self.route_planner_flag else None,
            'mobile_app_flag': self.mobile_app_flag,
            'route_planner_flag': self.route_planner_flag,
            'subscribe_flag': self.subscribe_flag,
        }
        return result

    def __str__ (self):
        return self.description_en


DATA = []  # type: List[Data]


def load_data () -> None:
    """
    Loads the sensor data information to global variable DATA.

    The DATA variable is a list containing information about data collected by all sensor nodes.
    This data is stored in the database.
    It can be used in the route planner and/or in the mobile app, and it can be subscribed by any user.
    """
    global DATA
    with open ('/opt/expolis/etc/sensor_data', 'r') as fd:
        sensor_data = yaml.safe_load (fd)
    DATA = [
        Data (
            sql_identifier=d ['sql_identifier'],
            description_en=d ['description_en'],
            description_pt=d ['description_pt'],
            sql_type=d['sql_type'],
            mqtt_message_index=d ['mqtt_message_index'],
            pollution_profile_b=d.get ('pollution_profile_b'),
            pollution_profile_m=d.get ('pollution_profile_m'),
            mobile_app_flag=d ['mobile_app_flag'],
            route_planner_flag=d ['route_planner_flag'],
            subscribe_flag=d ['subscribe_flag'],
        )
        for d in sensor_data
    ]


def save_data ():
    with open ('/opt/expolis/etc/sensor_data', 'w') as fd:
        sensor_data = [
            d.to_dict ()
            for d in DATA
        ]
        yaml.safe_dump (sensor_data, fd)
