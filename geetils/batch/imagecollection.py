import ee


"""
Utilizing the static methods of Google Earth Engine's Python API this module includes functions to handle the process of exporting image collections.
"""


def _collection_to_local_hard_drive_exporter(collection, path: str = None, extension: str = 'zip', bandType: str = None, bandOrder: list = None, **kwargs: dict):
    """
    Description:
        Exports an image collection's images as Earth Engine assets.
    Arguments:
        collection  (ee.ImageCollection)    (mandatory): The collection of images.
        path        (str)                   (mandatory): The path to download the image. Defaults to None.
        extension   (str)                   (mandatory): Self-explanatory. Defaults to zip.
        bandType    (str)                   (mandatory): A dictionary from band name to band types.
        bandOrder   (list)                  (optional):  A list specifying the order of the bands in the result.
        kwargs      (dictionary)            (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
        -The following is an example value for the extension argument(e.g. type 'zip' and not '.zip').
    """
    exportTasksIdsList = []
    listOfImages = collection.toList(collection.size())
    size = listOfImages.size().getInfo()

    # client side loop.
    for counter in range(size):
        # typecasting is necessary
        imageToExport = ee.Image(listOfImages.get(counter))

        taskID = _export_image_to_local_hard_drive(imageToExport, kwargs, path, extension)

        exportTasksIdsList.append(taskID)
    return exportTasksIdsList


def _collection_to_asset_exporter(collection, bandType: str, kwargs: dict):
    """
    Description:
        Exports an image collection's images as Earth Engine assets.
    Arguments:
        collection  (ee.ImageCollection)    (mandatory): The collection of images.
        bandType    (str)                   (mandatory): A dictionary from band name to band types.
        bandOrder   (list)                  (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)                  (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
    """
    exportTasksIdsList = []
    listOfImages = collection.toList(collection.size())
    size = listOfImages.size().getInfo()

    # client side loop.
    for counter in range(size):
        # typecasting is necessary
        imageToExport = ee.Image(listOfImages.get(counter))

        taskID = _image_to_asset_exporter(imageToExport, bandType, bandOrder, kwargs)

        exportTasksIdsList.append(taskID)
    return exportTasksIdsList


def _collection_to_drive_exporter(collection, bandType: str, kwargs: dict):
    """
    Description:
        Creates a batch task to export an Image as a raster to Google Drive.
    Arguments:
        collection  (ee.ImageCollection)    (mandatory): The collection of images.
        bandType    (str)                   (mandatory): A dictionary from band name to band types.
        bandOrder   (list)                  (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)                  (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
    """
    exportTasksIdsList = []
    listOfImages = collection.toList(collection.size())
    size = listOfImages.size().getInfo()

    # client side loop.
    for counter in range(size):
        # typecasting is necessary
        imageToExport = ee.Image(listOfImages.get(counter))

        taskID = _image_to_drive_exporter(imageToExport, bandType, bandOrder, kwargs)

        exportTasksIdsList.append(taskID)
    return exportTasksIdsList


def _collection_to_cloud_storage_exporter(collection, bandType: str, kwargs: dict):
    """
    Description:
        Exports an image collection's images to Google Cloud Storage.
    Arguments:
        collection  (ee.ImageCollection)    (mandatory): The collection of images.
        bandType    (str)                   (mandatory): A dictionary from band name to band types.
        bandOrder   (list)                  (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)                  (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
    """
    exportTasksIdsList = []
    listOfImages = collection.toList(collection.size())
    size = listOfImages.size().getInfo()

    # client side loop.
    for counter in range(size):
        # typecasting is necessary
        imageToExport = ee.Image(listOfImages.get(counter))

        taskID = _image_to_cloud_storage_exporter(imageToExport, bandType, bandOrder, kwargs)

        exportTasksIdsList.append(taskID)
    return exportTasksIdsList

# https://gis.stackexchange.com/questions/307974/what-are-the-other-bits-in-sentinels-qa60-band
# https://forum.step.esa.int/t/sentinel-2-msi-level-1c-qa60-band/24884

# https://www.earthdatascience.org/tutorials/basic-polygon-operations-google-earth-engine/
