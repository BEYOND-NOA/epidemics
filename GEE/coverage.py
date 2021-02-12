import ee  # import the Earth Engine Python Package.
import configparser
import geetils_standard  # import the custom gee api.

# the Python API package must be initialized for every new session and script alike.
ee.Initialize()


def main():
    # read configuration file
    config = configparser.RawConfigParser()
    config.read("/home/lazarikos/Documents/PycharmProjects/EarthEngine/WNV_DATA/monthly/api/settings/settings.ini")

    configuration = {
        "crs": config["Landsat7"]["crs"],
        "aoi": config["Areas_EPSG4326"]["ITA_SECOND_GENERATION"],
        "startDate": config["Landsat8"]["startDate"],
        "endDate": config["Landsat8"]["endDate"],
    }

    # create the aoi
    configAOI = configuration["aoi"]
    coordinates = configAOI.split(",")
    coordinates[:] = list(map(float, coordinates))

    aoi = ee.Geometry.Polygon(coordinates, configuration["crs"])

    # create the collection
    landsat7Collection = geetils_standard._collection_creator("LANDSAT/LE07/C01/T1_SR", configuration["startDate"], configuration["endDate"], aoi)

    # print coverage
    geetils_standard._landsat_coverage(landsat7Collection)


if __name__ == "__main__":
    main()
