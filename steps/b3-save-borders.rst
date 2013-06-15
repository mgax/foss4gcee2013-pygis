Step B3 - save borders
======================
Save borders to shapefile.

.. code:: python

    def calculate_borders():
        # ...
        borders_layer_defn = borders_layer.GetLayerDefn()
        for a, geom_a in enumerate(geometries):
            for b, geom_b in enumerate(geometries):
                # ...
                wkt = shapely.wkt.dumps(common_border)
                border_feature = ogr.Feature(borders_layer_defn)
                border_feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
                borders_layer.CreateFeature(border_feature)

    def main():
        # ...
        borders = shp_driver.CreateDataSource('output/borders.shp')
        borders_layer = borders.CreateLayer('layer', wgs84)
        calculate_borders(borders_layer)
        borders.Destroy()
        # ...
