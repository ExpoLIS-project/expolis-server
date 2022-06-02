# language=markdown
"""
Provides an enumeration of space resolutions.

The enumeration is represented by class `Resolution`.
Objects of this class are used to:

* generate SQL tables and functions that deal with data aggregated in different space resolutions;
* insert data in SQL tables that contain data aggregated in different space resolutions.

The variable `RESOLUTIONS` contains a list of spatial resolutions that are used in the EXPOLIS project.
"""


class Resolution:
    """
    Represents a space resolution.
    """
    def __init__ (
            self,
            sql_identifier: str,
            description: str,
            cell_latitude_size: float,
            cell_longitude_size: float,
            ):
        """
        Sole const
        :param sql_identifier: the string used in SQL tables and functions that deal with space resolutions.
        """
        self.sql_identifier = sql_identifier
        self.description = description
        self.cell_latitude_size = cell_latitude_size
        self.cell_longitude_size = cell_longitude_size

    def __str__(self):
        return self.description


FIFTY_METERS = Resolution (
    sql_identifier='fifty_meters',
    description='50m',
    cell_latitude_size=0.000557031249997,
    cell_longitude_size=0.000630859374999,
)

HUNDRED_METERS = Resolution (
    sql_identifier='hundred_meters',
    description='100m',
    cell_latitude_size=0.0011157255601,
    cell_longitude_size=0.00125914938003,
)

THOUSAND_METERS = Resolution (
    sql_identifier='thousand_meters',
    description='1000m',
    cell_latitude_size=0.0090082251600340,
    cell_longitude_size=0.0114938390815770 ,
)

RESOLUTIONS = [
    HUNDRED_METERS,
    THOUSAND_METERS,
]

RESOLUTION_DICT = {
    '100': HUNDRED_METERS,
    '1000': THOUSAND_METERS,
}
