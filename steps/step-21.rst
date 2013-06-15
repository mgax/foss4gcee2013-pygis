Step 21
=======
Save number of hikers who go to each park.

::

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
