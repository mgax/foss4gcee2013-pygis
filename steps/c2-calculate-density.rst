Step C2 - calculate density
===========================
Calculate hiker density (people per square kilometer) for each park. We
make use of the fact that `stereo70` coordinates are measured in meters;
the calculated area is good enough for our purpose.

.. code:: python

    def calculate_density(parks_layer, hikers):
        for i in range(parks_layer.GetFeatureCount()):
            park_in = parks_layer.GetFeature(i)
            name = park_in.GetField('nume')
            park_geom = park_in.GetGeometryRef()
            area = park_geom.Area()
            people = hikers.get(name, 0)
            density = people / (area / 10**6)
            print density
