import ee
import math # this module provides access to the mathematical functions defined by the C standard.
import textwrap


# ------------------------------------------------------------------------------------------------------


def _collection_creator(argument, startDate, endDate, geometry):
    return ee.ImageCollection(argument) \
        .filterDate(startDate, endDate) \
        .filterBounds(geometry)


def _band_selector(image, bandsList):
    bands = ee.Image(image).bandNames()
    bands2 = bands.removeAll(bandsList)
    return image.select(bands2)


def _date_extractor(collection):
    def innerFunction(image, newList):
        date = image.date().format("YYYY-MM-dd")
        newList = ee.List(newList)
        return ee.List(newList.add(date).distinct().sort())

    return collection.iterate(innerFunction, ee.List([]))


def _landsat_coverage(collection):
    def inner_function(path):
        return ee.List(collection.filter(ee.Filter.eq('WRS_PATH', path)).aggregate_array('WRS_ROW').distinct().sort())

    wrsPathsList = (collection.aggregate_array('WRS_PATH')).distinct()
    wrsRowsList = wrsPaths.map(inner_function)

    print("", wrsPathsList)
    print("", wrsRowsList)


def _temporal_collection(collection, properties, acquisitionDates, interval, units):
    if units not in ["year", "month", "week", "day", "hour", "minute", "second"]:
        raise ValueError("units must be one of 'year','month','week','day','hour','minute', or 'second'.")

    def inner_function(i):
        # Get the start date of the current sequence.
        startDate = ee.Date(acquisitionDates.get(i))
        # Get the end date of the current sequence.
        endDate = ee.Date(acquisitionDates.get(i)).advance(interval, units)

        mosaiced = collection.filterDate(startDate, endDate).mosaic()
        mosaiced = mosaiced.copyProperties(collection.filterDate(startDate, endDate).first(), properties)
        return mosaiced

    acquisitionDates = ee.List(acquisitionDates)
    # Create a sequence of numbers, one for each time interval.
    sequence = ee.List.sequence(0, ee.Number(acquisitionDates.size()).subtract(1))

    return ee.ImageCollection(sequence.map(inner_function))


def _export_collection_toCloudStorage(collection, aoi, bucket, crs, scale, fileFormat, maxPixels, description):
    # variable declaration.
    exportTasksIdsList = []
    listOfImages = collection.toList(collection.size())
    size = listOfImages.size().getInfo()

    # client side loop.
    for counter in range(size):
        # typecasting is necessary
        imageToExport = ee.Image(listOfImages.get(counter))

        # export task creation.
        task = ee.batch.Export.image.toCloudStorage(
            region=aoi,
            image=imageToExport,
            bucket=bucket,
            description=ee.String(imageToExport.get(description)).getInfo(),
            crs=crs,
            scale=scale,
            fileFormat=fileFormat,
            maxPixels=maxPixels
        )

        # Start the export task.
        task.start()
        exportTasksIdsList.append(task.id)
    return exportTasksIdsList


def _export_collection_toDrive(collection, aoi, bucket, crs, scale, fileFormat, maxPixels, description):
    # variable declaration.
    exportTasksIdsList = []
    listOfImages = collection.toList(collection.size())
    size = listOfImages.size().getInfo()

    # client side loop.
    for counter in range(size):
        # typecasting is necessary
        imageToExport = ee.Image(listOfImages.get(counter))

        # export task creation
        task = ee.batch.Export.image.toDrive(
            region=aoi,
            image=imageToExport,
            folder=bucket,
            description=ee.String(imageToExport.get(description)).getInfo(),
            crs=crs,
            scale=scale,
            fileFormat=fileFormat,
            maxPixels=maxPixels
        )

        # Start the export task.
        task.start()
        exportTasksIdsList.append(task.id)
    return exportTasksIdsList


# ------------------------------------------------------------------------------------------------------

def _l7_help():
    prefix = "\t"
    preferredWidth = 70
    wrapper = textwrap.TextWrapper(initial_indent=prefix, width=preferredWidth, subsequent_indent=2 * prefix)
    print(wrapper.fill("_l7_ndbi_calculator"))
    print(wrapper.fill("_l7_ndmi_calculator"))
    print(wrapper.fill("_l7_ndmi_calculator"))
    print(wrapper.fill("_l7_ndvi_calculator"))
    print(wrapper.fill("_l7_ndwi_calculator"))
    print(wrapper.fill("_l7_ndwi_calculator"))


def _l7_ndbi_calculator(image):
    ndbi = image.normalizedDifference(["B5", "B4"]).rename("NDBI").toDouble()
    return ndbi


def _l7_ndmi_calculator(image):
    ndmi = image.normalizedDifference(["B4", "B5"]).rename("NDMI").toDouble()
    return ndmi


def _l7_ndvi_calculator(image):
    ndvi = image.normalizedDifference(["B4", "B3"]).rename("NDVI").toDouble()
    return ndvi


def _l7_ndwi_calculator(image):
    ndwi = image.normalizedDifference(["B2", "B5"]).rename("NDWI").toDouble()
    return ndwi


def _spatial_interpolation(image, radius, kernelType, units, iterations):
    filled = image.focal_mean(radius, kernelType, units, iterations)  # larger values means greater blurring on the data.
    result = ee.Image(filled).blend(image)  # blend the focal_mean result with the initial input image.
    result = result.copyProperties(image, ee.Image(image).propertyNames())
    return ee.Image(result)


def _l7_sr_cloudMask(image):
    qa = image.select('pixel_qa')
    # If the cloud bit (5) is set and the cloud confidence (7) is high
    # or the cloud shadow bit is set (3), then it's a bad pixel.
    cloud = qa.bitwiseAnd(1 << 5) \
        .And(qa.bitwiseAnd(1 << 7)) \
        .Or(qa.bitwiseAnd(1 << 3))
    # Remove edge pixels that don't occur in all bands
    mask2 = image.mask().reduce(ee.Reducer.min())
    return image.updateMask(cloud.Not()).updateMask(mask2)


# ------------------------------------------------------------------------------------------------------


def _l8_help():
    prefix = "\t"
    preferredWidth = 70
    wrapper = textwrap.TextWrapper(initial_indent=prefix, width=preferredWidth, subsequent_indent=2 * prefix)
    print(wrapper.fill("_l8_ndbi_calculator(image)"))
    print(wrapper.fill("_l8_ndmi_calculator(image)"))
    print(wrapper.fill("_l8_ndvi_calculator(image)"))
    print(wrapper.fill("_l8_ndwi_calculator(image)"))
    print(wrapper.fill("_l8_sr_cloudMask(image)"))


def _l8_ndbi_calculator(image):
    ndbi = image.normalizedDifference(["B6", "B5"]).rename("NDBI").toDouble()
    return ndbi


def _l8_ndmi_calculator(image):
    ndmi = image.normalizedDifference(["B5", "B6"]).rename("NDMI").toDouble()
    return ndmi


def _l8_ndvi_calculator(image):
    ndvi = image.normalizedDifference(["B5", "B4"]).rename("NDVI").toDouble()
    return ndvi


def _l8_ndwi_calculator(image):
    ndwi = image.normalizedDifference(["B3", "B6"]).rename("NDWI").toDouble()
    return ndwi


def _l8_sr_cloudMask(image):
    # Bits 3 and 5 are cloud shadow and cloud, respectively.
    cloudShadowBitMask = 1 << 3
    cloudsBitMask = 1 << 5

    # Get the pixel QA band.
    qa = image.select('pixel_qa')

    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(qa.bitwiseAnd(cloudsBitMask).eq(0))

    return image.updateMask(mask)

# --------------------------------------------------------------------------------
