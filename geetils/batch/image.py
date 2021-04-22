import ee
import os
import tqdm
import requests


"""
Utilizing the static methods of Google Earth Engine's Python API this module includes functions to handle the process of exporting image collections.
"""


def _image_to_local_hard_drive_exporter(image, kwargs: dict, path: str = None, extension: str = 'zip'):
    """
    Description:
        Creates a batch task to export an image as a raster to the local hard drive.
    Arguments:
        image       (ee.Image)  (mandatory): The image to export.
        path        (str)       (mandatory): The path to download the image. Defaults to None.
        extension   (str)       (mandatory): Self-explanatory. Defaults to zip.
        bandType    (str)       (mandatory): A dictionary from band name to band types.
        bandOrder   (list)      (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)      (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -If the path value is not defined the image will be downloaded to the same folder as the script.
        -The function does not check for the validity of the provided options so caution needs to be exercised.
        -The following is an example value for the extension argument(e.g. type 'zip' and not '.zip').

        Quick overview of what each status code means:
        1XX - Information
        2XX - Success
        3XX - Redirect
        4XX - Client Error (you messed up)
        5XX - Server Error (they messed up)
    """
    if not bool(kwargs) or image.get("description").getInfo() is None:
        raise ValueError("Either an image does not have a description property or no parameters were specified for the image export task")

    if path is None:
        path = os.getcwd()

    # get the url
    url = image.getDownloadURL(kwargs)

    # request data
    try:
        response = requests.get(url)
        response.raise_for_status()  # If the response was successful, no Exception will be raised
    except requests.exceptions.HTTPError as error:
        raise SystemExit(error)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)

    fileSize = int(response.headers.get('content-length', 0))  # Total size in bytes.

    # if fileSize >= float(3e+9):  # 3GB TOO_LONG
    #     print("Please try again in few moments.")
    #     response.close()
    #     sys.exit()

    blockSize = 1024  # 1 MB

    fileProgressBar = tqdm.tqdm(total=fileSize, desc=image.get("description").getInfo(), unit='kB', position=1, unit_scale=True, leave=True)

    # write the contents of the variable into a file.
    with open('{}/{}.{}'.format(path, image.get("description").getInfo(), extension), 'wb') as file:
        for block in response.iter_content(blockSize):
            file.write(block)
            fileProgressBar.update(len(block))
        # file.write(response.content)
        file.close()
    response.close()
    fileProgressBar.close()


def _image_to_asset_exporter(image, bandType: str, kwargs: dict):
    """
    Description:
        Creates a batch task to export an Image as a raster to an Earth Engine asset.
    Arguments:
        image       (ee.Image)  (mandatory): The image to export.
        bandType    (str)       (mandatory): A dictionary from band name to band types.
        bandOrder   (list)      (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)      (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
    """
    if not bool(kwargs) or image.get("description").getInfo() is None:
        raise ValueError("Either an image does not have a description property or no parameters were specified for the image export task")

    # Error: Exported bands must have compatible data types. found inconsistent types.
    bandTypes = ee.List.repeat(bandType, image.bandNames().size())
    bandDictionary = ee.Dictionary.fromLists(image.bandNames(), bandTypes)

    image = image.cast(bandDictionary)

    # export task creation.
    task = ee.batch.Export.image.toAsset(image=image, description=image.get("description").getInfo(), **kwargs)
    # Start the export task.
    task.start()
    return task.id


def _image_to_drive_exporter(image, bandType: str, kwargs: dict):
    """
    Description:
        Creates a batch task to export an Image as a raster to Google Drive.
    Arguments:
        image       (ee.Image)  (mandatory): The image to export.
        bandType    (str)       (mandatory): A dictionary from band name to band types.
        bandOrder   (list)      (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)      (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
    """
    if not bool(kwargs) or image.get("description").getInfo() is None:
        raise ValueError("Either an image does not have a description property or no parameters were specified for the image export task")

    # Error: Exported bands must have compatible data types. found inconsistent types.
    bandTypes = ee.List.repeat(bandType, image.bandNames().size())
    bandDictionary = ee.Dictionary.fromLists(image.bandNames(), bandTypes)

    image = image.cast(bandDictionary)

    # export task creation.
    task = ee.batch.Export.image.toDrive(image=image, description=image.get("description").getInfo(), **kwargs)
    # Start the export task.
    task.start()
    return task.id


def _image_to_cloud_storage_exporter(image, bandType: str, kwargs: dict):
    """
    Description:
        Creates a batch task to export an Image as a raster to Google Drive.
    Arguments:
        image       (ee.Image)  (mandatory): The image to export.
        bandType    (str)       (mandatory): A dictionary from band name to band types.
        bandOrder   (list)      (optional):  A list specifying the order of the bands in the result.
        kwargs      (dict)      (optional):  Dictionary of optional parameters.
    Notes:
        -The argument bandType must be one of: 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
        'uint32', 'byte', 'short', 'int', 'long', 'float' and 'double'.
        -If bandTypes includes bands that are not already in the input image, they will be added to the image as transparent bands.
        -If the argument bandOrder is specified, must match the full list of bands in the result.
        -If the argument bandOrder isn't also specified, new bands will be appended in alphabetical order.
        -All images to be exported must contain a field named "description".
        -The function does not check for the validity of the provided options so caution needs to be exercised.
    """
    if not bool(kwargs) or image.get("description").getInfo() is None:
        raise ValueError("Either an image does not have a description property or no parameters were specified for the image export task")

    # Error: Exported bands must have compatible data types. found inconsistent types.
    bandTypes = ee.List.repeat(bandType, image.bandNames().size())
    bandDictionary = ee.Dictionary.fromLists(image.bandNames(), bandTypes)

    image = image.cast(bandDictionary)

    # export task creation.
    task = ee.batch.Export.image.toCloudStorage(image=image, description=image.get("description").getInfo(), **kwargs)
    # Start the export task.
    task.start()
    return task.id
