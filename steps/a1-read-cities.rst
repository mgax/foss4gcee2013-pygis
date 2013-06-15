Step A1 - read city polygons
============================
Load city shapefile; print names. Use separate function to keep the code
readable later on.

.. code:: python

    import ogr

    def calculate_hikers(cities_layer):
        for i in range(cities_layer.GetFeatureCount()):
            city = cities_layer.GetFeature(i)
            city_centroid = city_geom.Centroid()
            print city.GetField('uat_name_n'), city_centroid

    def main():
        cities = ogr.Open('input/ro_cities.shp')
        cities_layer = cities.GetLayer(0)
        calculate_hikers(cities_layer)
        cities.Destroy()
