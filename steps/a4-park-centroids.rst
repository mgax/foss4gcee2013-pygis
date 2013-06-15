Step A4 - park centroids
========================
Calculate and store park centroids in memory. The parks shapefile is
projected in `stereo70`, aka `EPSG:31700`_, the Romanian national
projection, so we'll transform it to `wgs84`.

.. _`EPSG:31700`: http://spatialreference.org/ref/epsg/31700/

.. code:: python

    import osr

    stereo70 = osr.SpatialReference()
    stereo70.ImportFromEPSG(31700)
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    stereo70_to_wgs84 = osr.CoordinateTransformation(stereo70, wgs84)

    def load_parks_data(parks_layer):
        parks_data = []
        for i in range(parks_layer.GetFeatureCount()):
            park = parks_layer.GetFeature(i)
            park_centroid = park.GetGeometryRef().Centroid()
            park_centroid.Transform(stereo70_to_wgs84)
            parks_data.append({
                'centroid': park_centroid,
                'name': park.GetField('nume'),
            })
        return parks_data

    def main():
        # ...
        parks = ogr.Open('input/ro_natparks.shp')
        parks_layer = parks.GetLayer(0)
        parks_data = load_parks_data(parks_layer)
        # ...
