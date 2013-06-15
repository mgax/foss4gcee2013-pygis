Step A2 - read CSV data for population
======================================
Load CSV data. We receive strings, and need to perform conversion to
integers. `population` is a `dict` object, basically a hash table.

.. code:: python

    import csv

    def load_population_data():
        population = {}
        with open('input/population.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                population[int(row['siruta'])] = int(row['populatie'])
        return population

    def main():
        population = load_population_data()
        print population
        # ...
