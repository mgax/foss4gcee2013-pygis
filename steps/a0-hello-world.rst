Step A0 - hello world
=====================
"Hello world" program. Save the text in a file named ``hikers.py`` and
run it with ``python hikers.py`` from the command-line.

All our code is run from the main() function. This is good practice, it
allows other scripts to import functions from our module, without
accidentally running anything.

.. code:: python

    def main():
        print "hello world"

    if __name__ == '__main__':
        main()
