import ee
import datetime
import tabulate
ee.Initialize()


REDUCERS = {
    "firstNonNull": ee.Reducer.firstNonNull(),
    "lastNonNull": ee.Reducer.lastNonNull(),
    "median": ee.Reducer.median(),
    "mean": ee.Reducer.mean(),
    "min": ee.Reducer.min()
}

REDUCERPATTERNS = {
    "firstNonNull": "_first",
    "lastNonNull": "_last",
    "median": "_median",
    "mean": "_mean",
    "min": "_min"
}


def _temporal_collection_creator(collection, specifiedReducer, firstDatesList, secondDatesList, timeFormat: str = "YYYY-MM-dd",
                                 timeZone: str = "UTC"):
    """
    Description:
      Returns an ee.List of image composites.
    Arguments:
      collection        (ee.ImageCollection)  (mandatory): Self-explanatory.
      specifiedReducer  (ee.Reducer)          (mandatory): The ee.Reducer to apply.
      firstDatesList    (list)                (mandatory): A list containing the start dates of each sub date-range.
      secondDatesList   (list)                (mandatory): A list containing the end dates of each sub date-range.
      timeFormat        (str)                 (mandatory): A datetime pattern. Defaults to "YYYY-MM-dd".
      timeZone          (str)                 (mandatory): The time zone. Defaults to "UTC".
    Notes:
      -The datetime pattern is  described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html
    """
    # Developer Notes:
    # By default resultant band names of the ".reduce(ee.Reducer.'reducer name')" functions will have the name of the reducer appended.
    # This is taken care of and band names are renamed once more to revome the trailing suffix.

    # Create a sequence of numbers, one for each time interval.
    sequence = ee.List.sequence(0, ee.Number(firstDatesList.size()).subtract(1))

    def _inner_function(temp, imagesList):
        imagesList = ee.List(imagesList)
        # Get the start date of the current sequence.
        startDate = ee.Date(firstDatesList.get(temp))
        # Get the end date of the current sequence.
        endDate = ee.Date(secondDatesList.get(temp))

        temporalCollection = collection.filterDate(startDate, endDate)
        formattedAcquisitionDate = temporalCollection.first().date().format(timeFormat, timeZone)

        # Apply the specified reducer and remove the trailing _"reducer name" from each image's bands.
        image = temporalCollection.reduce(REDUCERS[specifiedReducer])
        oldImageBands = image.bandNames()
        newImageBands = oldImageBands.map(lambda bandName: ee.String(bandName).replace(REDUCERPATTERNS[specifiedReducer], ''))
        image = image.select(oldImageBands).rename(newImageBands)

        image = image.set("system:time_start", formattedAcquisitionDate)
        return imagesList.add(image)

    return ee.List(sequence.iterate(_inner_function, ee.List([])))


def _spatial_interpolation(image, radius: float = 1.5, kernelType: str = "circle", kernelUnit: str = "pixels", iterations: int = 1, kernel=None):
    """
    Description:
        Applies a morphological mean filter to each band of an image using a named or custom kernel.
    Arguments:
        image       (ee.Image)      (mandatory): The image to which to apply the operations.
        radius      (float)         (optional):  The radius of the kernel to use. Defaults to 1.5.
        kernelType  (str)           (optional):  The type of kernel to use. Defaults to circle.
        kernelUnit  (str)           (optional):  If a kernel is not specified, this determines the kernel's unit.
        iterations  (int)           (optional):  The number of times to apply the given kernel. Defaults to 1
        kernel      (ee.Kernel)     (optional):  A custom kernel. If used, kernelType and radius are ignored. Defaults to None.
    Notes:
        -Argument kernelUnit must be one of: 'meters', 'pixels'.
        -Argument kernelType argument must be one of: 'circle', 'square', 'cross', 'plus', octagon' and 'diamond'.
        -It is worth adjusting the radius and iteration parameters. The larger these values the greater the blurring on the data.
        -Argument kernel defaults to None. If you parse anything in here you will override the kernelType parameter.
    """
    filled = image.focal_mean(radius, kernelType, kernelUnit, iterations, kernel)
    result = ee.Image(filled).blend(image)  # blend the focal_mean result with the initial input image.
    result = result.copyProperties(image, ee.Image(image).propertyNames())
    return ee.Image(result)


def _sentinel2_coverage(collection):
    """
    Description:
        Depicts a table containing information about the image collection.
        Table columns:
            Orbit:  The relative orbit number.
            Tiles:  The mgrs tiles.
            Dates:  The acquisition dates.
    Arguments:
        collection  (ee.ImageCollection)    (mandatory): Self-explanatory.
    Notes:
        None.
    """
    headers = ["Orbit", "Tiles", "Dates"]

    def _inner_function(orbit, collectionProperty: str):
        return collection.filter(ee.Filter.eq('SENSING_ORBIT_NUMBER', orbit)).aggregate_array(collectionProperty).distinct().sort()

    def _inner_date_formatter(tempIndex):
        tempList = ee.List(datesList.get(tempIndex))
        return tempList.map(lambda date: ee.Date(date).format("YYYY-mm-dd"))

    sensingOrbitNumbersList = collection.aggregate_array('SENSING_ORBIT_NUMBER').distinct()

    mgrsTilesList = sensingOrbitNumbersList.map(lambda orbit: _inner_function(orbit, "MGRS_TILE"))
    datesList = sensingOrbitNumbersList.map(lambda orbit: _inner_function(orbit, "system:time_start"))

    dateListSequence = ee.List.sequence(0, datesList.size().subtract(1))

    datesList = dateListSequence.map(_inner_date_formatter)

    table = zip(sensingOrbitNumbersList.getInfo(), mgrsTilesList.getInfo(), datesList.getInfo())
    print(tabulate.tabulate(table, headers=headers, floatfmt=".4f"))


def _landsat_coverage(collection):
    """
    Description:
        Depicts a table containing information about the image collection.
        Table columns:
            Orbit:  The relative orbit number.
            Tiles:  The mgrs tiles.
            Dates:  The acquisition dates.
    Arguments:
        collection  (ee.ImageCollection)    (mandatory): Self-explanatory.
    Notes:
        None.
    """
    headers = ["Orbit", "Tiles", "Dates"]

    def _inner_function(path, collectionProperty: str):
        return collection.filter(ee.Filter.eq('WRS_PATH', path)).aggregate_array(collectionProperty).distinct().sort()

    def _inner_date_formatter(tempIndex):
        tempList = ee.List(datesList.get(tempIndex))
        return tempList.map(lambda date: ee.Date(date).format("YYYY-mm-dd"))

    wrsPathsList = collection.aggregate_array('WRS_PATH').distinct()
    wrsRowsList = wrsPathsList.map(lambda path: _inner_function(path, "WRS_ROW"))
    datesList = wrsPathsList.map(lambda path: _inner_function(path, "system:time_start"))

    dateListSequence = ee.List.sequence(0, datesList.size().subtract(1))

    datesList = dateListSequence.map(_inner_date_formatter)

    table = zip(wrsPathsList.getInfo(), wrsRowsList.getInfo(), datesList.getInfo())
    print(tabulate.tabulate(table, headers=headers, floatfmt=".4f"))


def _export_tasks_viewer(exportTasksIdsList, tableFormat: str = "plain"):
    """
    Description:
      Depicts a table containing information about the export tasks passed.
    Table columns:
      -id: the id of the image export task.
      -state:  the current state of the image export task.
      -type:   the type of the export task.
      -description:    self-explanatory.
      -error:  the cause for the failure of the process, in case of its failure.
    Arguments:
      exportTasksIdsList: (list)  (mandatory): the list of export tasks.
      tableFormat:        (str)   (optional): The table format which will be used for the display. Defaults to "plain".
    Notes:
      -Argument tableFormat must be one of: "simple", "plain", "grid", "fancy_grid", "github", "pipe", "orgtbl", "jira",
      "presto", "psql", "rst", "mediawiki", "moinmoin", "youtrack", "html", "latex", "latex_raw", "latex_booktabs", "tsv", "textile".
    """
    taskInfoList = []
    tableHeaders = ["Task_Id", "Task_State", "Task_Type", "Task_Attempt", "Task_Description", "Queue_Time", "Execution_Time", "Completion_Time",
                    "Error_Message"]
    tableFormats = ["simple", "plain", "grid", "fancy_grid", "github", "pipe", "orgtbl", "jira", "presto", "psql", "rst",
                    "mediawiki", "moinmoin", "youtrack", "html", "latex", "latex_raw", "latex_booktabs", "tsv", "textile"]

    if tableFormat not in tableFormats:
        raise ValueError("Parameter tableFormat must be one of {}".format(tableFormats))

    # populate taskInfoList.
    for exportTaskId in exportTasksIdsList:

        taskState = ee.data.getTaskStatus(exportTaskId)[0]["state"]
        taskType = ee.data.getTaskStatus(exportTaskId)[0]["task_type"]
        taskDescription = ee.data.getTaskStatus(exportTaskId)[0]["description"]

        startTaskTimestamp = datetime.datetime.fromtimestamp(ee.data.getTaskStatus(exportTaskId)[0]["start_timestamp_ms"] / 1000.0)
        updateTaskTimestamp = datetime.datetime.fromtimestamp(ee.data.getTaskStatus(exportTaskId)[0]["update_timestamp_ms"] / 1000.0)
        creationTaskTimestamp = datetime.datetime.fromtimestamp(ee.data.getTaskStatus(exportTaskId)[0]["creation_timestamp_ms"] / 1000.0)

        queueTime = None
        taskAttempt = None
        executionTime = None
        completionTime = None

        if taskState not in ["READY", "RUNNING"]:
            queueTime = (startTaskTimestamp - creationTaskTimestamp).total_seconds()
            executionTime = (updateTaskTimestamp - startTaskTimestamp).total_seconds()

        if taskState == "COMPLETED":
            taskAttempt = ee.data.getTaskStatus(exportTaskId)[0]["attempt"]
            completionTime = (updateTaskTimestamp - creationTaskTimestamp).total_seconds()

        try:
            errorMessage = ee.data.getTaskStatus(exportTaskId)[0]["error_message"]
        except KeyError:
            errorMessage = None  # this just means that the export task has not failed.

        taskInfoList.append([exportTaskId, taskState, taskType, taskAttempt, taskDescription, queueTime, executionTime, completionTime, errorMessage])

    # table display.
    table = tabulate.tabulate(taskInfoList, headers=tableHeaders, tablefmt=tableFormat)
    print(table)
