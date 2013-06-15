Step 2
======
Load CSV data.

::

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
