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

modisCollection = ee.ImageCollection([])  # the filtered collection of images.
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


# function for the selection of the desired bands.
def _modis_products_bands_selector(image):
    # create a new image from the indices.
    processedImage = ee.Image(geetils_standard._band_selector(image, ["LST_Day_1km", "QC_Day", "LST_Night_1km", "QC_Night"])).toDouble()

    # copy the original image's properties.
    processedImage = processedImage.copyProperties(image, ee.Image(image).propertyNames())

    return processedImage


# description image property creation.
def _description_creator(image):
    splitted = ee.String(image.get("system:id")).split("/")
    
    description = ee.String(splitted.get(0)).cat("_").cat(splitted.get(2)).cat("_") \
        .cat(ee.String(splitted.get(3)).replace("_", "-", "g")) \
        .cat("_").cat(splitted.get(1))

    image = image.set("description", description)
    return image


def _load_configuration(iniFilePath):
    config = configparser.RawConfigParser()
    config.read(iniFilePath)

    configuration = {
        "startDate": config["Modis"]["startDate"],
        "endDate": config["Modis"]["endDate"],
        "monthlyStep": config["Modis"]["monthlyStep"],
        "crs": config["Modis"]["crs"],
        "scale": config["Modis"]["scale"],
        "bucket": config["Modis"]["bucket"],
        "fileFormat": config["Modis"]["fileFormat"],
        "maxPixels": config["Modis"]["maxPixels"],
        "aoi": config["Areas_EPSG4326"][config["Modis"]["area"]],
    }
    return configuration


def _image_export_task_scheduler(startDatesList, endDatesList, aoi, bucket, crs, scale, fileFormat, maxPixels):
    # global variables.
    global acquisitionDates
    global metritis
    global modisCollection
    global exportTasksIdsList
    global failedExportTasksList
    global cancelledExportTasksList

    # get the current start and end dates from the start date and end date period lists respectively.
    startPeriod = ee.Date(startDatesList[metritis])
    endPeriod = ee.Date(endDatesList[metritis])

    # informational message.
    print(time.ctime())
    print("Creating the sub image collection from", startDatesList[metritis], "till", endDatesList[metritis], ".")

    # image collection creation.
    modisCollection = geetils_standard._collection_creator("MODIS/006/MOD11A1", startPeriod, endPeriod, aoi) \
        .map(lambda image: _image_clipper(ee.Image(image), aoi)) \
        .map(lambda image: _modis_products_bands_selector(image)) \
        .map(lambda image: _description_creator(ee.Image(image)))

    # informational message.
    print("Found", modisCollection.size().getInfo(), "images.")

    acquisitionDates = ee.List(geetils_standard._date_extractor(modisCollection))

    # informational message.
    print("The corresponding images were taken these dates:", acquisitionDates.getInfo())

    if modisCollection.size().getInfo() > 0:

        # informational message.
        print("Submitting the image export tasks.")

        # export the image collection.
        exportTasksIdsList = geetils_standard._export_collection_toCloudStorage(modisCollection, aoi, bucket, crs, scale, fileFormat, maxPixels,
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
        modisCollection = ee.ImageCollection([])

        # call the _image_export_task_scheduler function again.
        _image_export_task_scheduler(startDatesList, endDatesList, wrsDictionary, aoi, bucket, crs, scale, fileFormat, maxPixels)


def main():
    # load configuration.
    configuration = _load_configuration("/home/lazarikos/Documents/PycharmProjects/EarthEngine/WNV_DATA/monthly/api/settings/settings.ini")

    # area of interest.
    configAOI = configuration["aoi"]
    coordinates = configAOI.split(",")
    coordinates[:] = list(map(float, coordinates))

    aoi = ee.Geometry.Polygon(coordinates, configuration["crs"])

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

    # Informational introductory message.
    print("This run will attempt to create an image collection from", str(datesList[0]), "till",
        datesList[-1], "of MOD11A1.006 Terra Land Surface Temperature and Emissivity Daily Global 500m images.\n")

    # list of datetimes to a list of strings conversion.
    datesListStr = [date.strftime("%Y-%m-%d") for date in datesList]

    # creation of the final two dates lists.
    startDatesList = datesListStr[:-1]  # minus the last element of datesList.
    endDatesList = datesListStr[1:]  # minus the first element of datesList.

    # the fun stuff.
    _image_export_task_scheduler(startDatesList, endDatesList, aoi, configuration["bucket"], configuration["crs"],
                                 int(configuration["scale"]), configuration["fileFormat"], float(configuration["maxPixels"]))

    print("Done!")
    if cancelledExportTasksList:
        print("Cancelled image export tasks:", cancelledExportTasksList)
    if failedExportTasksList:
        print("Failed image export tasks:")
        for key, value in failedExportTasksList.items():
            print("{} : {}".format(key, value))


if __name__ == "__main__":
    main()
