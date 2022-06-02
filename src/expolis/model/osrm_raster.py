

class ConfigOSRMRaster:

    def __init__(
            self,
            min_longitude: float, min_latitude: float,
            max_longitude: float, max_latitude: float,
            num_rows: int, num_cols: int,
            weight_osrm: float, weight_pollution: float):
        self.min_longitude = min_longitude
        self.min_latitude = min_latitude
        self.max_longitude = max_longitude
        self.max_latitude = max_latitude
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.weight_osrm = weight_osrm
        self.weight_pollution = weight_pollution

    def save (self):
        with open ('/opt/expolis/etc/config-osrm-raster', 'w') as fd:
            fd.write ('{} {}\n'.format (self.min_longitude, self.min_latitude))
            fd.write ('{} {}\n'.format (self.max_longitude, self.max_latitude))
            fd.write ('{} {}\n'.format (self.num_cols, self.num_rows))
            fd.write ('{} {}\n'.format (self.weight_osrm, self.weight_pollution))


def load_config_osrm_raster () -> ConfigOSRMRaster:
    with open ('/opt/expolis/etc/config-osrm-raster', 'r') as fd:
        values_line1 = fd.readline ().split (' ')
        values_line2 = fd.readline ().split (' ')
        values_line3 = fd.readline ().split (' ')
        values_line4 = fd.readline ().split (' ')
    return ConfigOSRMRaster (
        min_longitude=float (values_line1 [0]),
        min_latitude=float (values_line1 [1]),
        max_longitude=float (values_line2 [0]),
        max_latitude=float (values_line2 [1]),
        num_cols=int (values_line3 [1]),
        num_rows=int (values_line3 [0]),
        weight_osrm=float (values_line4 [0]),
        weight_pollution=float (values_line4 [1]),
    )
