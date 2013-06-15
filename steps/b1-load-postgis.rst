Step B1 - load from PostGIS
===========================
Load data from PostGIS. We only print the first 30 characters of each
geometry since they are quite long. The geometries are fetched as plain
strings in the `WKT format`_ (well-known text).

.. _wkt format: http://en.wikipedia.org/wiki/Well-known_text

.. code:: python

    import psycopg2

    def calculate_borders():
        conn = psycopg2.connect(dbname='natural_earth2', user='user')
        cursor = conn.cursor()
        cursor.execute("SELECT name,ST_AsText(the_geom) "
                       "FROM ne_10m_admin_1_states_provinces_shp "
                       "WHERE iso_a2='RO'")
        for row in cursor:
            print row[0], row[1][:30]+'...'

        conn.close()

    def main():
        # ...
        calculate_borders()
        # ...
