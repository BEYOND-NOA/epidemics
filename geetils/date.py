import ee

"""
Utilizing the static methods of Google Earth Engine's Python API this module includes functions to handle the process of creating custom date ranges.
"""


def _acquisition_date_extractor(collection, dateProperty: str, timeFormat: str = "YYYY-MM-dd", timeZone: str = "UTC"):
    """
  Description:
    Returns a sorted ee.List of distinct acquisition dates.
  Arguments:
    collection  (ee.Image/ee.ImageCollection)   (mandatory):  The image collection.
    timeFormat  (str)                           (mandatory):  A datetime pattern. Defaults to None.
    timeZone    (str)                           (mandatory):  The time zone (e.g. 'America/Los_Angeles'). Defaults to UTC.
  Notes:
    -List of time zones:  https://www.joda.org/joda-time/timezones.html
    -Reference for Joda-Time format characters:  http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html
  """

    def _inner_function(image, newList):
        date = ee.Date(image.get(dateProperty)).format(timeFormat, timeZone)
        newList = ee.List(newList)
        return newList.add(date)

    # typecasting to retrieve the result as an ee.List and not computedObject.
    return ee.List(collection.iterate(_inner_function, ee.List([]))).distinct().sort()


def _date_range_creator_from_dates(startDate, endDate, interval: int = 1, unit: str = "month", timeZone: str = "UTC"):
    """
  Description:
    Returns an ee.List of ee.DateRange objects by increments of interval in specified units.
  Arguments:
    startDate   (ee.Date)   (mandatory): the start date.
    endDate     (ee.Date)   (mandatory): the end date.
    interval    (int)       (optional): self-explanatory. Defaults to 1.
    unit        (str)       (optional): specified unit type to advance. Defaults to month.
    timeZone    (str)       (optional): the time zone in which to interpret the start and end dates. Defaults to UTC.
  Notes:
    -An example ee.DateRange object follows: {"type": "DateRange", "dates": [1546300800000, 1548979200000]}.
    -Argument unit must be one of "year", "month" "week", "day", "hour", "minute", or "second".
  """

    def _inner_function(temp, dateRangeList):
        dateRangeList = ee.List(dateRangeList)
        firstDate = startDate.advance(ee.Number(interval).multiply(temp), unit, timeZone)
        lastDate = firstDate.advance(interval, unit, timeZone)
        return dateRangeList.add(ee.DateRange(firstDate, lastDate, timeZone))

    units = ["year", "month", "week", "day", "hour", "minute", "second"]
    if unit not in units:
        raise ValueError("Parameter unit must be one of {}".format(units))

    # get the difference between the start and end date in the specified unit.
    rangeDifference = endDate.difference(startDate, unit)
    # determine the multiplicity of interval.
    rangeTotal = rangeDifference.divide(interval).toInt()

    # rangeSequence = ee.List.sequence(0, ee.Number(rangeTotal))
    rangeSequence = ee.List.sequence(0, ee.Number(rangeTotal).subtract(1))
    return ee.List(rangeSequence.iterate(_inner_function, ee.List([])))


def _date_range_creator_from_list(datesList, interval: int = 1, unit: str = "month", timeFormat: str = "YYYY-MM-dd", timeZone: str = "UTC"):
    """
  Description:
    Returns an ee.List of ee.DateRange objects by increments of interval in specified units.
  Arguments:
    endDate     (ee.List)   (mandatory): An ee.List of dates.
    interval    (int)       (optional): self-explanatory. Defaults to 1.
    unit        (str)       (optional): specified unit type to advance. Defaults to month.
    timeZone    (str)       (optional): the time zone in which to interpret the start and end dates. Defaults to UTC.
  Notes:
    -An example ee.DateRange object follows: {"type": "DateRange", "dates": [1546300800000, 1548979200000]}.
    -Argument unit must be one of "year", "month" "week", "day", "hour", "minute", or "second".
  """

    def _inner_function(temp, secondDateList):
        secondDateList = ee.List(secondDateList)
        return secondDateList.add(ee.Date(datesList.get(temp)).advance(interval, unit, timeZone).format(timeFormat, timeZone))

    units = ["year", "month", "week", "day", "hour", "minute", "second"]
    if unit not in units:
        raise ValueError("Parameter unit must be one of {}".format(units))

    dateSequence = ee.List.sequence(0, datesList.size().subtract(1))

    return ee.List(dateSequence.iterate(_inner_function, ee.List([])))
