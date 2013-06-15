Step 4
======
Calculate and store park centroids.

::

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
