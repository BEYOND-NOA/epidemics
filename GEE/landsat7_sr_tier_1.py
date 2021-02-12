# import the necessary modules.
import ee  # import the Earth Engine Python Package.
import time  # this module provides various time-related functions.
import calendar  # this module provides useful functions related to the calendar.
import datetime  # this module supplies classes for manipulating dates and times.
import configparser

import geetils_standard  # import the custom gee api.

# the Python API package must be initialized for every new session and script alike.
# authentication however is a one time action.
ee.Initialize()

# global variables declaration & initialization.
metritis = 0  # counter variable, used to fetch the start and end dates of each time period.

landsat7Collection = ee.ImageCollection([])  # the filtered collection of images.
acquisitionDates = ee.List([])

# declare and initialize other helpful stuff.
exportTasksIdsList = []  # record the status of the submitted image export tasks.
failedExportTasksList = {}  # record every failed image export task (for whatever reason).
cancelledExportTasksList = []  # record every cancelled image export task (for whatever reason).


# clip an image.
def _image_clipper(image, AOI):
    return image.clip(AOI)


# fragmentation of the time period of interest, into smaller monthly chunks.
def _advance_months(sourceDate, months):
    month = sourceDate.month - 1 + months
    year = sourceDate.year + month // 12
    month = month % 12 + 1
    day = min(sourceDate.day, calendar.monthrange(year, month)[1])

    return datetime.datetime(year, month, day)


# function for the generation of the desired indices from the image bands.
def _landsat7_products_indices_creator(image):
    # normalized indices creation.
    ndbi = geetils_standard._l7_ndbi_calculator(image)
    ndmi = geetils_standard._l7_ndmi_calculator(image)
    ndvi = geetils_standard._l7_ndvi_calculator(image)
    ndwi = geetils_standard._l7_ndwi_calculator(image)

    # normalized indixes only image creation.
    processedImage = ee.Image([ndvi, ndwi, ndmi, ndbi])

    # copy the original image's properties.
    processedImage = processedImage.copyProperties(image, ee.Image(image).propertyNames())

    return processedImage


# description image property creation.
def _description_creator(image):
    splitted = ee.String(image.get("LANDSAT_ID")).split("_")

    description = ee.String(splitted.get(0)).cat("_").cat(splitted.get(1)) \
        .cat("_") \
        .cat(ee.String(splitted.get(3)).slice(0, 4)).cat("-") \
        .cat(ee.String(splitted.get(3)).slice(4, 6)).cat("-") \
        .cat(ee.String(splitted.get(3)).slice(6, 8)).cat("_") \
        .cat(splitted.get(5)).cat("_") \
        .cat(splitted.get(6)).cat("_") \
        .cat(ee.Number(image.get("WRS_PATH")).int().format())

    image = image.set("description", description)
    return image


# read the .ini file parameters.
def _load_configuration(iniFilePath):
    config = configparser.RawConfigParser()
    config.read(iniFilePath)

    configuration = {
        "wrs": config.items("Landsat7_WRS"),

        "kernelRadius": config["Landsat7_kernel"]["radius"],
        "kernelType": config["Landsat7_kernel"]["type"],
        "kernelUnits": config["Landsat7_kernel"]["units"],
        "iterations": config["Landsat7_kernel"]["iterations"],

        "startDate": config["Landsat7"]["startDate"],
        "endDate": config["Landsat7"]["endDate"],
        "monthlyStep": config["Landsat7"]["monthlyStep"],
        "crs": config["Landsat7"]["crs"],
        "scale": config["Landsat7"]["scale"],
        "bucket": config["Landsat7"]["bucket"],
        "fileFormat": config["Landsat7"]["fileFormat"],
        "maxPixels": config["Landsat7"]["maxPixels"],
        "aoi": config["Areas_EPSG4326"][config["Landsat7"]["area"]]
    }
    return configuration


def _image_export_task_scheduler(startDatesList, endDatesList, wrsDictionary, aoi, bucket, crs, scale, fileFormat, maxPixels,
                                 kernelRadius, kernelType, kernelUnits, iterations):
    # global variables.
    global acquisitionDates
    global metritis
    global landsat7Collection
    global exportTasksIdsList
    global failedExportTasksList
    global cancelledExportTasksList

    # get the current start and end dates from the start date and end date period lists respectively.
    startPeriod = ee.Date(startDatesList[metritis])
    endPeriod = ee.Date(endDatesList[metritis])

    # informational message.
    print(time.ctime())
    print("Creating the sub image collection from", startDatesList[metritis], "till", endDatesList[metritis], ".")

    # initial image collection creation.
    initialLandsat7Collection = geetils_standard._collection_creator("LANDSAT/LE07/C01/T1_SR", startPeriod, endPeriod, aoi)

    # further filtering the initial image collection.
    for key, value in wrsDictionary.items():
        tempLandsat7Collection = initialLandsat7Collection \
            .filter(ee.Filter.Or(
            ee.Filter.And(ee.Filter.eq("WRS_PATH", key), ee.Filter.inList("WRS_ROW", value))
        ))
        landsat7Collection = landsat7Collection.merge(tempLandsat7Collection)

    landsat7Collection = landsat7Collection \
        .map(lambda image: _image_clipper(ee.Image(image), aoi)) \
        .map(lambda image: geetils_standard._l7_sr_cloudMask(ee.Image(image))) \
        .map(lambda image: _description_creator(image))

    # informational message.
    print("Found", landsat7Collection.size().getInfo(), "images.")
    print("Attempting to create daily mosaics from the existing images.")

    acquisitionDates = ee.List(geetils_standard._date_extractor(landsat7Collection))

    # informational message.
    print("The corresponding images were taken these dates:", acquisitionDates.getInfo())

    # create the collection of mosaics from the image collection.
    mosaicCollection = geetils_standard._temporal_collection(landsat7Collection, ["description"], acquisitionDates, 1, "day")

    # create the indices, clip the images.
    mosaicCollection = mosaicCollection.map(lambda image: _landsat7_products_indices_creator(ee.Image(image)))
    # attempt to cover the gaps created by the SLC failure.
    mosaicCollection = mosaicCollection.map(lambda image: geetils_standard._spatial_interpolation(ee.Image(image), kernelRadius, kernelType,
                                                                                                  kernelUnits, iterations))

    # informational message.
    print("Current image collection is reduced to", mosaicCollection.size().getInfo(), "images.")

    # the image collection is NOT empty for the current time period.
    if mosaicCollection.size().getInfo() > 0:
        # informational message.
        print("Submitting the image export tasks.")

        # export the image collection.
        exportTasksIdsList = geetils_standard._export_collection_toCloudStorage(mosaicCollection, aoi, bucket, crs, scale, fileFormat, maxPixels,
                                                                                "description")

        # informational message.
        print("Executing the image export tasks.")

        # as long as there are still export tasks running:
        while len(exportTasksIdsList) > 0:
            # wait for 10 seconds.
            time.sleep(10)

            for taskId in exportTasksIdsList:
                state = ee.data.getTaskStatus(taskId)[0]["state"]

                # if the current task is completed, remove it from the dictionary.
                if state == "COMPLETED":
                    exportTasksIdsList.remove(taskId)

                elif state == "CANCEL_REQUESTED" or state == "CANCELLED":
                    exportTasksIdsList.remove(taskId)
                    cancelledExportTasksList.append(ee.data.getTaskStatus(taskId)[0]["description"])

                elif state == "FAILED":
                    exportTasksIdsList.remove(taskId)
                    # error_message: Failure reason. Appears only if state is FAILED.
                    failedExportTasksList[ee.data.getTaskStatus(taskId)[0]["description"]] = ee.data.getTaskStatus(taskId)[0]["error_message"]

            # if there are no more image export tasks for the current time period.
            if len(exportTasksIdsList) == 0:

                print("Completed image export tasks from", startDatesList[metritis], "till", endDatesList[metritis], ".")
                print("Total cancelled image export tasks:", len(cancelledExportTasksList))
                print("Total failed image export tasks:", len(failedExportTasksList), "\n")

            else:  # as long as there are still image export tasks currently executing.
                print("Not done yet:", len(exportTasksIdsList), "image export tasks still remaining.")
    else:
        # informational message.
        print("No images were found for the current time period. Consequently no task will be submitted.\n")

    # the image collection is empty for the current time period.
    metritis = metritis + 1

    # as long as there are still date periods to be checked.
    if metritis < len(startDatesList):
        # clear the collection.
        landsat7Collection = ee.ImageCollection([])

        # call the _image_export_task_scheduler function again.
        _image_export_task_scheduler(startDatesList, endDatesList, wrsDictionary, aoi, bucket, crs, scale, fileFormat, maxPixels,
                                     kernelRadius, kernelType, kernelUnits, iterations)


def main():
    # load configuration.
    configuration = _load_configuration("/home/lazarikos/Documents/PycharmProjects/EarthEngine/WNV_DATA/monthly/api/settings/settings.ini")

    # area of interest.
    configAOI = configuration["aoi"]
    coordinates = configAOI.split(",")
    coordinates[:] = list(map(float, coordinates))

    aoi = ee.Geometry.Polygon(coordinates, configuration["crs"])

    # wrs.
    wrsDictionary = {int(key): list(map(int, value.split(","))) for key, value in dict(configuration["wrs"]).items()}

    # dates.
    configStartDate = configuration["startDate"]
    configEndDate = configuration["endDate"]

    startDate = datetime.datetime.strptime(configStartDate, "%Y-%m-%d")
    endDate = datetime.datetime.strptime(configEndDate, "%Y-%m-%d")
    # temporal assignment.
    currentDate = startDate

    # a list containing the start, end and all the intermediate dates.
    datesList = []
    while True:
        datesList.append(currentDate)
        # advance specified number of months forward.
        currentDate = _advance_months(currentDate, int(configuration["monthlyStep"]))

        # break section.
        if currentDate > endDate:
            break

    # list of datetimes to a list of strings conversion.
    datesListStr = [date.strftime("%Y-%m-%d") for date in datesList]

    # creation of the final two dates lists.
    startDatesList = datesListStr[:-1]  # minus the last element of datesList.
    endDatesList = datesListStr[1:]  # minus the first element of datesList.

    # Informational introductory message.
    print(time.ctime())
    print("This run will attempt to create an image collection from", datesList[0], "till", datesList[-1],
          "of USGS Landsat 7 SR Reflectance Tier 1 images.\n")

    # the fun stuff.
    _image_export_task_scheduler(startDatesList, endDatesList, wrsDictionary, aoi, configuration["bucket"], configuration["crs"],
                                 int(configuration["scale"]), configuration["fileFormat"], float(configuration["maxPixels"]),
                                 int(configuration["kernelRadius"]), configuration["kernelType"], configuration["kernelUnits"],
                                 int(configuration["iterations"]))

    # Informational completion message.
    print("Done!")
    if cancelledExportTasksList:
        print("Cancelled image export tasks:", cancelledExportTasksList)
    if failedExportTasksList:
        print("Failed image export tasks:")
        for key, value in failedExportTasksList.items():
            print("{} : {}".format(key, value))


if __name__ == "__main__":
    main()
