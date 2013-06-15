import os
import sys
import csv
from collections import defaultdict
from decimal import Decimal as D
import shutil
import ogr
import osr
import pyproj
import shapely.wkt
import psycopg2


MAX_LAZINESS_DISTANCE = 50000  # 50 Km
HIKER_FRACTION = 0.01  # 1%

stereo70 = osr.SpatialReference()
stereo70.ImportFromEPSG(31700)
wgs84 = osr.SpatialReference()
wgs84.ImportFromEPSG(4326)
stereo70_to_wgs84 = osr.CoordinateTransformation(stereo70, wgs84)
geod = pyproj.Geod(ellps='WGS84')
shp_driver = ogr.GetDriverByName('ESRI Shapefile')


def load_population_data():
    population = {}
    with open('input/population.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            population[int(row['siruta'])] = int(row['populatie'])
    return population


def load_parks_data(parks_layer):
    parks_data = []
    for i in range(parks_layer.GetFeatureCount()):
        park = parks_layer.GetFeature(i)
        park_centroid = park.GetGeometryRef().Centroid()
        park_centroid.Transform(stereo70_to_wgs84)
        parks_data.append({
            'centroid': park_centroid,
            'name': park.GetField('nume'),
        })
    return parks_data


def calculate_hikers(cities_layer, flux_layer, population, parks_data,
                      max_distance):
    flux_layer_defn = flux_layer.GetLayerDefn()
    hikers = defaultdict(int)
    for i in range(cities_layer.GetFeatureCount()):
        city = cities_layer.GetFeature(i)
        city_population = population[city.GetField('siruta')]
        city_geom = city.GetGeometryRef()
        city_centroid = city_geom.Centroid()
        city_centroid.Transform(stereo70_to_wgs84)
        #print city.GetField('uat_name_n'), city_population, city_centroid
        nearby_parks = []
        for park in parks_data:
            park_centroid = park['centroid']
            (angle1, angle2, distance) = geod.inv(
                city_centroid.GetX(), city_centroid.GetY(),
                park_centroid.GetX(), park_centroid.GetY())

            if distance < max_distance:
                #print '-->', park['name'], park_centroid
                nearby_parks.append(park)

        if nearby_parks:  # do people have a park nearby?
            hiker_population = city_population * HIKER_FRACTION
            people_per_park = int(hiker_population / len(nearby_parks))
            for park in nearby_parks:
                park_centroid = park['centroid']
                line_feature = ogr.Feature(flux_layer_defn)
                line_feature.SetField('people', people_per_park)
                line = ogr.Geometry(ogr.wkbLineString)
                line.AddPoint(city_centroid.GetX(), city_centroid.GetY())
                line.AddPoint(park_centroid.GetX(), park_centroid.GetY())
                line_feature.SetGeometry(line)
                flux_layer.CreateFeature(line_feature)
                hikers[park['name']] += people_per_park

    return dict(hikers)


def calculate_density(parks_layer, densities_layer, hikers):

    densities_layer_defn = densities_layer.GetLayerDefn()
    for i in range(parks_layer.GetFeatureCount()):
        park_in = parks_layer.GetFeature(i)
        name = park_in.GetField('nume')
        park_geom = park_in.GetGeometryRef()
        area = park_geom.Area()
        people = hikers.get(name, 0)
        #density = float(D(people / (area / 10**6)).quantize(D('.01')))
        density = people / (area / 10**6)
        park_out = ogr.Feature(densities_layer_defn)
        park_out.SetField('name', name)
        park_out.SetField('visitors', people)
        park_out.SetField('density', density)
        park_out.SetGeometry(park_geom)
        densities_layer.CreateFeature(park_out)


def calculate_borders(borders_layer):
    conn = psycopg2.connect(dbname='natural_earth2', user='user')
    cursor = conn.cursor()
    cursor.execute("SELECT name,ST_AsText(the_geom) "
                   "FROM ne_10m_admin_1_states_provinces_shp "
                   "WHERE iso_a2='RO'")
    geometries = []
    for row in cursor:
        geom = shapely.wkt.loads(row[1])
        geometries.append(geom)

    borders_layer_defn = borders_layer.GetLayerDefn()
    for a, geom_a in enumerate(geometries):
        for b, geom_b in enumerate(geometries):
            if b <= a:
                continue
            common_border = geom_a.intersection(geom_b)
            if common_border.is_empty:
                continue
            wkt = shapely.wkt.dumps(common_border)
            border_feature = ogr.Feature(borders_layer_defn)
            border_feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
            borders_layer.CreateFeature(border_feature)

    conn.close()


def main():
    print "loading data"
    population = load_population_data()
    max_distance = int(sys.argv[1])

    if os.path.isdir('output'):
        shutil.rmtree('output')
    os.mkdir('output')

    parks = ogr.Open('input/ro_natparks.shp')
    parks_layer = parks.GetLayer(0)
    parks_data = load_parks_data(parks_layer)

    cities = ogr.Open('input/ro_cities.shp')
    cities_layer = cities.GetLayer(0)

    print "distributing hikers"
    flux = shp_driver.CreateDataSource('output/flux.shp')
    flux_layer = flux.CreateLayer('layer', wgs84)
    flux_layer.CreateField(ogr.FieldDefn('people', ogr.OFTInteger))
    hikers = calculate_hikers(cities_layer, flux_layer, population, parks_data,
                              max_distance)
    flux.Destroy()

    print "calculating hiker density"
    densities = shp_driver.CreateDataSource('output/densities.shp')
    densities_layer = densities.CreateLayer('layer', stereo70)
    densities_layer.CreateField(ogr.FieldDefn('name', ogr.OFTString))
    densities_layer.CreateField(ogr.FieldDefn('visitors', ogr.OFTInteger))
    densities_layer.CreateField(ogr.FieldDefn('density', ogr.OFTReal))
    calculate_density(parks_layer, densities_layer, hikers)
    densities.Destroy()

    print "calculating borders"
    borders = shp_driver.CreateDataSource('output/borders.shp')
    borders_layer = borders.CreateLayer('layer', wgs84)
    calculate_borders(borders_layer)
    borders.Destroy()

    cities.Destroy()
    parks.Destroy()

    print 'done'


if __name__ == '__main__':
    main()
