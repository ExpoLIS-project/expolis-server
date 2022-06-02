import psycopg2


class Database:
    def __init__ (self, database=None, username=None):
        with open ('/opt/expolis/etc/config-database', 'r') as fd:
            aux = fd.readline () [:-1]
            if database is None:
                database = aux
            aux = fd.readline () [:-1]
            if username is None:
                username = aux
            password = fd.readline () [:-1]
        self.connection = psycopg2.connect (
            dbname=database,
            user=username,
            password=password
        )  # type: psycopg2.extensions.connection
        self.cursor = self.connection.cursor ()  # type: psycopg2.extensions.cursor

    def __del__ (self):
        self.cursor.close ()
        self.connection.commit ()
        self.connection.close ()


DATABASE_SENSOR = 'sensor_data'
DATABASE_OSM = 'osm_data'
ROLE_ADMIN = 'expolis_admin'
ROLE_APP = 'expolis_app'
ROLE_PHP = 'expolis_php'
