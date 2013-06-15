import os
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


def cleanup_shapefile(shapefile_path):
    assert shapefile_path.endswith('.shp')
    base_path, ext = os.path.splitext(shapefile_path)
    for ext in ['.shp', '.prj', '.shx', '.dbf']:
        file_path = base_path + ext
        if os.path.exists(file_path):
            os.remove(file_path)


def copy_attribute_definition(in_layer, out_layer):
    in_feature = in_layer.GetNextFeature()
    in_layer_defn = in_layer.GetLayerDefn()
    for i in range(in_layer_defn.GetFieldCount()):
        field_def = in_layer_defn.GetFieldDefn(i)
        out_layer.CreateField(field_def)
    in_layer.ResetReading()  # reset features read cursor


def calculate_centroids(in_layer, out_layer):
    copy_attribute_definition(in_layer, out_layer)
    in_layer_defn = in_layer.GetLayerDefn()
    in_feature = in_layer.GetNextFeature()
    out_layer_defn = out_layer.GetLayerDefn()
    while in_feature is not None:
        out_feature = ogr.Feature(out_layer_defn)
        # copy attributes
        for i in range(in_layer_defn.GetFieldCount()):
            out_feature.SetField(
                in_layer_defn.GetFieldDefn(i).GetNameRef(),
                in_feature.GetField(i))

        # calculate centroid
        in_geometry = in_feature.GetGeometryRef()
        centroid = in_geometry.Centroid()
        out_feature.SetGeometry(centroid)
        out_layer.CreateFeature(out_feature)

        # continue to next feature
        in_feature = in_layer.GetNextFeature()


def calculate_bounding_boxes(in_layer, out_layer):
    copy_attribute_definition(in_layer, out_layer)
    in_layer_defn = in_layer.GetLayerDefn()
    in_feature = in_layer.GetNextFeature()
    out_layer_defn = out_layer.GetLayerDefn()
    while in_feature is not None:
        out_feature = ogr.Feature(out_layer_defn)
        # copy attributes
        for i in range(in_layer_defn.GetFieldCount()):
            out_feature.SetField(
                in_layer_defn.GetFieldDefn(i).GetNameRef(),
                in_feature.GetField(i))

        # calculate bounding box
        in_geometry = in_feature.GetGeometryRef()
        minx, maxx, miny, maxy = in_geometry.GetEnvelope()
        linear_ring = ogr.Geometry(ogr.wkbLinearRing)
        linear_ring.AddPoint(minx, miny)
        linear_ring.AddPoint(maxx, miny)
        linear_ring.AddPoint(maxx, maxy)
        linear_ring.AddPoint(minx, maxy)
        linear_ring.AddPoint(minx, miny)
        bbox = ogr.Geometry(ogr.wkbPolygon)
        bbox.AddGeometry(linear_ring)
        out_feature.SetGeometry(bbox)
        out_layer.CreateFeature(out_feature)

        # continue to next feature
        in_feature = in_layer.GetNextFeature()


def calculate_nearby_parks_for_cities(city_centroids_layer,
                                      natpark_centroids_layer,
                                      flux_layer):

    flux_layer.CreateField(ogr.FieldDefn('from', ogr.OFTString))
    flux_layer.CreateField(ogr.FieldDefn('to', ogr.OFTString))
    flux_layer.CreateField(ogr.FieldDefn('distance', ogr.OFTReal))
    flux_layer.CreateField(ogr.FieldDefn('people', ogr.OFTReal))
    flux_layer_defn = flux_layer.GetLayerDefn()

    park_visitors = defaultdict(int)

    city_centroid = city_centroids_layer.GetNextFeature()
    while city_centroid is not None:
        city_geom = city_centroid.GetGeometryRef()
        city_geom_stereo70 = (city_geom.GetX(), city_geom.GetY())
        city_geom.Transform(stereo70_to_wgs84)

        nearby_parks = []
        natpark_centroid = natpark_centroids_layer.GetNextFeature()
        while natpark_centroid is not None:
            natpark_geom = natpark_centroid.GetGeometryRef()
            natpark_geom_stereo70 = (natpark_geom.GetX(), natpark_geom.GetY())
            natpark_geom.Transform(stereo70_to_wgs84)

            (angle1, angle2, distance) = geod.inv(
                city_geom.GetX(), city_geom.GetY(),
                natpark_geom.GetX(), natpark_geom.GetY())

            if distance < MAX_LAZINESS_DISTANCE:
                nearby_parks.append({
                    'coords': natpark_geom_stereo70,
                    'from': city_centroid.GetField('uat_name_n'),
                    'to': natpark_centroid.GetField('nume'),
                    'distance': distance,
                })

            natpark_centroid = natpark_centroids_layer.GetNextFeature()

        if nearby_parks:  # do people have a park nearby?
            population = city_centroid.GetField('total_locu')
            hiker_population = population * HIKER_FRACTION
            people_per_park = int(hiker_population / len(nearby_parks))
            for park_info in nearby_parks:
                line_feature = ogr.Feature(flux_layer_defn)
                line_feature.SetField('from', park_info['from'])
                line_feature.SetField('to', park_info['to'])
                line_feature.SetField('distance', park_info['distance'])
                line_feature.SetField('people', people_per_park)
                line = ogr.Geometry(ogr.wkbLineString)
                line.AddPoint(*city_geom_stereo70)
                line.AddPoint(*park_info['coords'])
                line_feature.SetGeometry(line)
                flux_layer.CreateFeature(line_feature)
                park_visitors[park_info['to']] += people_per_park

        natpark_centroids_layer.ResetReading()
        city_centroid = city_centroids_layer.GetNextFeature()

    return dict(park_visitors)


def copy_parks_with_visitors(natparks_layer,
                             natpark_visitors_layer,
                             park_visitors):
    natpark_visitors_layer.CreateField(ogr.FieldDefn('visitors', ogr.OFTInteger))
    natpark_visitors_layer.CreateField(ogr.FieldDefn('density', ogr.OFTReal))
    natpark_visitors_layer.CreateField(ogr.FieldDefn('name', ogr.OFTString))
    natparks_layer_defn = natparks_layer.GetLayerDefn()
    natpark = natparks_layer.GetNextFeature()
    natpark_visitors_layer_defn = natpark_visitors_layer.GetLayerDefn()
    while natpark is not None:
        out_feature = ogr.Feature(natpark_visitors_layer_defn)
        name = natpark.GetField('nume')
        natpark_geom = natpark.GetGeometryRef()
        area = natpark_geom.Area()
        people = park_visitors.get(name, 0)
        density = float(D(people / (area / 10**6)).quantize(D('.01')))
        out_feature.SetField('name', name)
        out_feature.SetField('visitors', people)
        out_feature.SetField('density', density)
        out_feature.SetField('name', name)
        out_feature.SetGeometry(natpark_geom)
        natpark_visitors_layer.CreateFeature(out_feature)
        natpark = natparks_layer.GetNextFeature()
    print 'copy done'


def calculate_borders(in_layer, out_layer):
    out_layer_defn = out_layer.GetLayerDefn()
    for a in range(in_layer.GetFeatureCount()):
        for b in range(a+1, in_layer.GetFeatureCount()):
            feature_a = in_layer.GetFeature(a)
            geom_a = shapely.wkt.loads(feature_a.GetGeometryRef().ExportToWkt())
            feature_b = in_layer.GetFeature(b)
            geom_b = shapely.wkt.loads(feature_b.GetGeometryRef().ExportToWkt())
            common_border = geom_a.intersection(geom_b)
            if common_border.is_empty:
                continue
            wkt = shapely.wkt.dumps(common_border)
            out_feature = ogr.Feature(out_layer_defn)
            out_feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
            out_layer.CreateFeature(out_feature)
        break


def postgis_query():
    conn = psycopg2.connect(dbname='natural_earth2', user='user')
    cursor = conn.cursor()
    cursor.execute("SELECT name,ST_AsText(ST_Centroid(the_geom)) FROM ne_10m_admin_1_states_provinces_shp WHERE iso_a2='RO'")
    for row in cursor:
        print row


def main():
    # calculate centroids & bounding boxes for cities
    cities = ogr.Open('shapes/ro_city_census.shp')
    cities_layer = cities.GetLayer(0)

    city_centroids_path = 'shapes/city_centroids.shp'
    if os.path.exists(city_centroids_path):
        os.remove(city_centroids_path)
    city_centroids = shp_driver.CreateDataSource(city_centroids_path)
    city_centroids_layer = city_centroids.CreateLayer('layer', stereo70)
    calculate_centroids(cities_layer, city_centroids_layer)
    city_centroids.Destroy()

    city_bbox_path = 'shapes/city_bbox.shp'
    cleanup_shapefile(city_bbox_path)
    city_bbox = shp_driver.CreateDataSource(city_bbox_path)
    city_bbox_layer = city_bbox.CreateLayer('layer', stereo70)
    calculate_bounding_boxes(cities_layer, city_bbox_layer)
    city_bbox.Destroy()

    cities.Destroy()

    # calculate centroids for natparks
    natparks = ogr.Open('shapes/ro_nat_park.shp')
    natparks_layer = natparks.GetLayer(0)
    natpark_centroids_path = 'shapes/natpark_centroids.shp'
    cleanup_shapefile(natpark_centroids_path)
    natpark_centroids = shp_driver.CreateDataSource(natpark_centroids_path)
    natpark_centroids_layer = natpark_centroids.CreateLayer('layer', stereo70)
    calculate_centroids(natparks_layer, natpark_centroids_layer)
    natpark_centroids.Destroy()
    natparks.Destroy()

    # calculate distances between cities and nearby natural parks
    city_centroids = ogr.Open('shapes/city_centroids.shp')
    city_centroids_layer = city_centroids.GetLayer(0)
    natpark_centroids = ogr.Open('shapes/natpark_centroids.shp')
    natpark_centroids_layer = natpark_centroids.GetLayer(0)
    flux_path = 'shapes/flux.shp'
    cleanup_shapefile(flux_path)
    flux = shp_driver.CreateDataSource(flux_path)
    flux_layer = flux.CreateLayer('layer', stereo70)
    park_visitors = calculate_nearby_parks_for_cities(
        city_centroids_layer,
        natpark_centroids_layer,
        flux_layer)
    flux.Destroy()
    natpark_centroids.Destroy()
    city_centroids.Destroy()

    # crete a new natparks layer, with number of visitors in each park
    natparks = ogr.Open('shapes/ro_nat_park.shp')
    natparks_layer = natparks.GetLayer(0)
    natpark_visitors_path = 'shapes/natpark_visitors.shp'
    cleanup_shapefile(natpark_visitors_path)
    natpark_visitors = shp_driver.CreateDataSource(natpark_visitors_path)
    natpark_visitors_layer = natpark_visitors.CreateLayer('layer', stereo70)
    copy_parks_with_visitors(natparks_layer,
                             natpark_visitors_layer,
                             park_visitors)
    natpark_visitors.Destroy()
    natparks.Destroy()

#    # extract county borders
#    counties = ogr.Open('shapes/judete_ro.shp')
#    counties_layer = counties.GetLayer(0)
#    borders_path = 'shapes/county_borders.shp'
#    cleanup_shapefile(borders_path)
#    borders = shp_driver.CreateDataSource(borders_path)
#    borders_layer = borders.CreateLayer('layer', stereo70)
#    calculate_borders(counties_layer, borders_layer)
#    borders.Destroy()
#    counties.Destroy()

    print 'were done here!'


def load_population_data():
    population = {}
    with open('input/population.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            population[int(row['siruta'])] = int(row['populatie'])
    return population


def load_parks_data():
    parks = ogr.Open('input/ro_natparks.shp')
    parks_layer = parks.GetLayer(0)
    parks_data = []
    for i in range(parks_layer.GetFeatureCount()):
        park = parks_layer.GetFeature(i)
        park_centroid = park.GetGeometryRef().Centroid()
        park_centroid.Transform(stereo70_to_wgs84)
        parks_data.append({
            'centroid': park_centroid,
            'name': park.GetField('nume'),
        })
    parks.Destroy()
    return parks_data


def calculate_hikers(cities_layer, flux_layer, population, parks_data):
    flux_layer_defn = flux_layer.GetLayerDefn()
    for i in range(cities_layer.GetFeatureCount()):
        city = cities_layer.GetFeature(i)
        city_population = population[city.GetField('siruta')]
        city_geom = city.GetGeometryRef()
        city_centroid = city_geom.Centroid()
        city_centroid.Transform(stereo70_to_wgs84)
        print city.GetField('uat_name_n'), city_population, city_centroid
        nearby_parks = []
        for park in parks_data:
            park_centroid = park['centroid']
            (angle1, angle2, distance) = geod.inv(
                city_centroid.GetX(), city_centroid.GetY(),
                park_centroid.GetX(), park_centroid.GetY())

            if distance < MAX_LAZINESS_DISTANCE:
                print '-->', park['name'], park_centroid
                nearby_parks.append(park_centroid)

        if nearby_parks:  # do people have a park nearby?
            hiker_population = city_population * HIKER_FRACTION
            people_per_park = int(hiker_population / len(nearby_parks))
            for destination in nearby_parks:
                line_feature = ogr.Feature(flux_layer_defn)
                line_feature.SetField('people', people_per_park)
                line = ogr.Geometry(ogr.wkbLineString)
                line.AddPoint(city_centroid.GetX(), city_centroid.GetY())
                line.AddPoint(destination.GetX(), destination.GetY())
                line_feature.SetGeometry(line)
                flux_layer.CreateFeature(line_feature)


def main():
    # calculate centroids & bounding boxes for cities
    population = load_population_data()

    parks_data = load_parks_data()

    if os.path.isdir('output'):
        shutil.rmtree('output')
    os.mkdir('output')

    cities = ogr.Open('input/ro_cities.shp')
    cities_layer = cities.GetLayer(0)

    flux = shp_driver.CreateDataSource('output/flux.shp')
    flux_layer = flux.CreateLayer('layer', wgs84)
    flux_layer.CreateField(ogr.FieldDefn('people', ogr.OFTReal))
    calculate_hikers(cities_layer, flux_layer, population, parks_data)
    flux.Destroy()

    cities.Destroy()
    print 'done'


if __name__ == '__main__':
    #postgis_query()
    main()

