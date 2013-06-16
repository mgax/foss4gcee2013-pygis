Step A3 - join with population
==============================
Join cities with population data. It's just a dictionary lookup.

.. code:: python

    def calculate_hikers(cities_layer, population):
        for i in range(cities_layer.GetFeatureCount()):
            # ...
            city_code = city.GetField('siruta')
            city_population = population[city_code]
            # ...
            print city.GetField('uat_name_n'), city_population, city_centroid
