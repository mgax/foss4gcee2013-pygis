Step C1 - count hikers per park
===============================
Save number of hikers who go to each park. defaultdict_ is an enhanced
`dict` that returns a default value if the requested key is missing. In
our case, the default value is ``int()``, which returns ``0``.

.. _defaultdict: http://docs.python.org/2/library/collections.html#collections.defaultdict

.. code:: python

    from collections import defaultdict

    def calculate_hikers(...):
        hikers = defaultdict(int)
        for i in range(cities_layer.GetFeatureCount()):
            # ...
            if nearby_parks:  # do people have a park nearby?
                # ...
                for park in nearby_parks:
                    # ...
                    hikers[park['name']] += people_per_park

        return dict(hikers)

    def main():
        # ...
        hikers = calculate_hikers(...)
        print hikers
        # ...
