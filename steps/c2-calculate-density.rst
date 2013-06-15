Step C2 - calculate density
===========================
Calculate hiker density for each park.

::

    def calculate_density(parks_layer, hikers):
        for i in range(parks_layer.GetFeatureCount()):
            park_in = parks_layer.GetFeature(i)
            name = park_in.GetField('nume')
            park_geom = park_in.GetGeometryRef()
            area = park_geom.Area()
            people = hikers.get(name, 0)
            density = people / (area / 10**6)
            print density
