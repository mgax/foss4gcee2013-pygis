Step 8
======
Parametrize the script.

::

    import sys

    def calculate_hikers(..., max_distance):
        # ...

    def main():
        max_distance = int(sys.argv[1])
        # ...
        hikers = calculate_hikers(..., max_distance)
