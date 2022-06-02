#!/usr/bin/env python3

from new_sensor_data import new_sensor_data

new_sensor_data (
    sql_identifier='co_1',
    sql_type='real',
    description_en='carbon monoxide 1/2',
    description_pt='monóxido de carbono 1/2',
    mobile_app_flag=True,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=6,
)

new_sensor_data (
    sql_identifier='co_2',
    sql_type='real',
    description_en='carbon monoxide 2/2',
    description_pt='monóxido de carbono 2/2',
    mobile_app_flag=False,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=7,
)

new_sensor_data (
    sql_identifier='no2_1',
    sql_type='real',
    description_en='nitric oxide 1/2',
    description_pt='óxido nitrico 1/2',
    mobile_app_flag=True,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=8,
)

new_sensor_data (
    sql_identifier='no2_2',
    sql_type='real',
    description_en='nitric oxide 2/2',
    description_pt='óxido nitrico 2/2',
    mobile_app_flag=False,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=9,
)

new_sensor_data (
    sql_identifier='pm1',
    sql_type='real',
    description_en='PM 1',
    description_pt='PM 1',
    mobile_app_flag=False,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=10,
)

new_sensor_data (
    sql_identifier='pm25',
    sql_type='real',
    description_en='PM 2.5',
    description_pt='PM 2.5',
    mobile_app_flag=False,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=11,
)

new_sensor_data (
    sql_identifier='pm10',
    sql_type='real',
    description_en='PM 10',
    description_pt='PM 10',
    mobile_app_flag=False,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=12,
)

new_sensor_data (
    sql_identifier='pm1f',
    sql_type='real',
    description_en='filtered PM 1',
    description_pt='PM 1 filtrado',
    mobile_app_flag=True,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=13,
)

new_sensor_data (
    sql_identifier='pm25f',
    sql_type='real',
    description_en='filtered PM 2.5',
    description_pt='PM 2.5 filtrado',
    mobile_app_flag=True,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=14,
)

new_sensor_data (
    sql_identifier='pm10f',
    sql_type='real',
    description_en='filtered PM 10',
    description_pt='PM 10 filtrado',
    mobile_app_flag=True,
    route_planner_flag=True,
    subscribe_flag=True,
    pollution_profile_m=1,
    pollution_profile_b=0,
    mqtt_message_index=15,
)

new_sensor_data (
    sql_identifier='temperature',
    sql_type='real',
    description_en='temperature',
    description_pt='temperatura',
    mobile_app_flag=True,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=16,
)

new_sensor_data (
    sql_identifier='pressure',
    sql_type='real',
    description_en='pressure',
    description_pt='pressão',
    mobile_app_flag=True,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=17,
)

new_sensor_data (
    sql_identifier='humidity',
    sql_type='real',
    description_en='humidity',
    description_pt='humidade',
    mobile_app_flag=True,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=18,
)

new_sensor_data (
    sql_identifier='kp',
    sql_type='real',
    description_en='Kp',
    description_pt='Kp',
    mobile_app_flag=False,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=21,
)

new_sensor_data (
    sql_identifier='kd',
    sql_type='real',
    description_en='Kd',
    description_pt='Kd',
    mobile_app_flag=False,
    route_planner_flag=False,
    subscribe_flag=True,
    pollution_profile_m=None,
    pollution_profile_b=None,
    mqtt_message_index=22,
)
