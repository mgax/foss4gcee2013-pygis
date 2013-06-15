Step A8 - script arguments
==========================
Parametrize the script.

.. code:: python

    import sys

    def calculate_hikers(..., max_distance, hiker_fraction):
        # ...

    def main():
        max_distance = int(sys.argv[1])
        hiker_fraction = float(sys.argv[2])
        # ...
        hikers = calculate_hikers(..., max_distance, hiker_fraction)
