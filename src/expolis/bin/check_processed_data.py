#!/usr/bin/env python3

import aggregation
import period
import resolution
import database
import data
from interpolation import INTERPOLATION_STATISTIC, INTERPOLATION_PERIOD, INTERPOLATION_RESOLUTION


def main ():
    data.load_data()
    db = database.Database ()
    for a_data in data.DATA:
        print ('Checking {}...'.format (a_data.description_en))
        for s in aggregation.STATISTICS:
            if not (a_data.mobile_app_flag or (a_data.route_planner_flag and s == INTERPOLATION_STATISTIC)):
                continue
            for p in period.PERIODS:
                if not (a_data.mobile_app_flag or (a_data.route_planner_flag and p == INTERPOLATION_PERIOD)):
                    continue
                for r in resolution.RESOLUTIONS:
                    if not (a_data.mobile_app_flag or (a_data.route_planner_flag and r == INTERPOLATION_RESOLUTION)):
                        continue
                    # language=SQL
                    sql_command = '''
SELECT DISTINCT date_trunc ('{date_trunc}', when_)
 FROM measurement_properties
 INNER JOIN {table_measurement}
    ON measurement_properties.ID = {table_measurement}.mpID
  WHERE date_trunc ('{date_trunc}', when_) NOT IN
 (SELECT when_ FROM {table_aggregation})'''.format (
                        sql_identifier=a_data.sql_identifier,
                        date_trunc=p.date_trunc,
                        table_measurement=a_data.table_measurement_name(),
                        table_aggregation=a_data.table_aggregation_name(
                            s=s,
                            p=p,
                            r=r
                        )
                    )
                    # language=SQL
                    sql_command = '''
WITH measurement_dates AS (
    SELECT date_trunc ('{date_trunc}', when_) AS period_
      FROM measurement_properties
      INNER JOIN {table_measurement}
        ON measurement_properties.ID = {table_measurement}.mpID
), measurement_periods AS (
    SELECT DISTINCT period_
      FROM measurement_dates
)
SELECT period_
  FROM measurement_periods
  WHERE period_ NOT IN
(SELECT when_ FROM {table_aggregation})'''.format (
                        sql_identifier=a_data.sql_identifier,
                        date_trunc=p.date_trunc,
                        table_measurement=a_data.table_measurement_name (),
                        table_aggregation=a_data.table_aggregation_name (
                            s=s,
                            p=p,
                            r=r
                        )
                    )
                    db.cursor.execute (sql_command)
                    first = True
                    for row in db.cursor:
                        if first:
                            first = False
                            print ('Measurements not in aggregated table {s} {p} {r}'.format (
                                s=s.description,
                                p=p.description,
                                r=r.description
                            ))
                        print (row [0], end=' ')
                    if not first:
                        print ()


if __name__ == '__main__':
    main ()
