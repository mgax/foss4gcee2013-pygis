Step A8 - script arguments
==========================
Expect two command-line arguments::

    python hikers.py 50000 0.01

This is a crude way to access the program's arguments. See argparse_ for
a more elegant solution.

.. _argparse: http://docs.python.org/2/howto/argparse.html

.. code:: python

    import sys

    def calculate_hikers(..., max_distance, hiker_fraction):
        # ...

    def main():
        max_distance = int(sys.argv[1])
        hiker_fraction = float(sys.argv[2])
        # ...
        hikers = calculate_hikers(..., max_distance, hiker_fraction)
