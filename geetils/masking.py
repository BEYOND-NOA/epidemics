import ee
import textwrap

"""
Utilizing the static methods of Google Earth Engine's Python API this module includes 
functions to handle the process of exporting image collections. 
"""

# SENTINEL2_L1C & SENTINEL2_L2A
BITS_SENTINEL2_BQA = {
    'cloud': {'10': 1},
    'cirrus': {'11': 1}
}

# SENTINEL2_L2A
BITS_SENTINEL2_SCL = {
    'saturated_or_defective': {'1': 1},
    'dark_area_pixels': {'2': 1},
    'cloud_shadows': {'3': 1},
    'vegetation': {'4': 1},
    'bare_soil': {'5': 1},
    'water': {'6': 1},
    'low_clouds_probability': {'7': 1},
    'medium_clouds_probability': {'8': 1},
    'high_clouds_probability': {'9': 1},
    'cirrus': {'10': 1},
    'snow_ice': {'11': 1}
}

# LANDSAT4_TOA & LANDSAT5_TOA & LANDSAT7_TOA
BITS_LANDSAT_BQA = {
    'cloud': {'4': 1},
    'low_cloud_confidence': {'5-6': 1},
    'medium_cloud_confidence': {'5-6': 2},
    'high_cloud_confidence': {'5-6': 3},
    'low_cloud_shadow_confidence': {'7-8': 1},
    'medium_cloud_shadow_confidence': {'7-8': 2},
    'high_cloud_shadow_confidence': {'7-8': 3},
    'low_snow_confidence': {'9-10': 1},
    'medium_snow_confidence': {'9-10': 2},
    'high_snow_confidence': {'9-10': 3}
}

# LANDSAT4_SR & LANDSAT5_SR & LANDSAT7_SR
BITS_LANDSAT_CLOUD_QA = {
    'dark_dense_vegetation': {'0': 1},
    'cloud': {'1': 1},
    'shadow': {'2': 1},
    'adjacent': {'3': 1},
    'snow': {'4': 1},
    'water': {'5': 1}
}

# LANDSAT4_SR & LANDSAT5_SR & LANDSAT7_SR
BITS_LANDSAT_PIXEL_QA = {
    'clear': {'1': 1},
    'water': {'2': 1},
    'shadow': {'3': 1},
    'snow': {'4': 1},
    'cloud': {'5': 1},
    'low_cloud_confidence': {'6-7': 1},
    'medium_cloud_confidence': {'6-7': 2},
    'high_cloud_confidence': {'6-7': 3}
}

# LANDSAT8_TOA
BITS_LANDSAT_BQA_L8 = {
    'cloud': {'4': 1},
    'low_cloud_confidence': {'5-6': 1},
    'medium_cloud_confidence': {'5-6': 2},
    'high_cloud_confidence': {'5-6': 3},
    'low_cloud_shadow_confidence': {'7-8': 1},
    'medium_cloud_shadow_confidence': {'7-8': 2},
    'high_cloud_shadow_confidence': {'7-8': 3},
    'low_snow_confidence': {'9-10': 1},
    'medium_snow_confidence': {'9-10': 2},
    'high_snow_confidence': {'9-10': 3},
    'low_cirrus_confidence': {'11-12': 1},
    'medium_cirrus_confidence': {'11-12': 2},
    'high_cirrus_confidence': {'11-12': 3}
}

# LANDSAT8_SR
BITS_LANDSAT_PIXEL_QA_L8 = {
    'clear': {'1': 1},
    'water': {'2': 1},
    'shadow': {'3': 1},
    'snow': {'4': 1},
    'cloud': {'5': 1},
    'low_cloud_confidence': {'6-7': 1},
    'medium_cloud_confidence': {'6-7': 2},
    'high_cloud_confidence': {'6-7': 3},
    'low_cirrus_confidence': {'8-9': 1},
    'medium_cirrus_confidence': {'8-9': 2},
    'high_cirrus_confidence': {'8-9': 3},
    'occlusion': {'10': 1}
}

# Cloud mask naming convention.
NAMING_CONVENTION = {
    "BITS_SENTINEL2_BQA": "QA60",
    "BITS_SENTINEL2_SLC": "SLC",
    "BITS_LANDSAT_BQA": "BQA",
    "BITS_LANDSAT_CLOUD_QA": "CLOUD_QA",
    "BITS_LANDSAT_PIXEL_QA": "PIXEL_QA",
    "BITS_LANDSAT_BQA_L8": "BQA",
    "BITS_LANDSAT_PIXEL_QA_L8": "PIXEL_QA"
}


def _help():
    """
    Description:
        Displays a helpful list of all the possible options for each available bit mask band.
    Arguments:
        None.
    Notes:
        None.
    """
    prefix = "\t"
    preferredWidth = 70
    wrapper = textwrap.TextWrapper(initial_indent=prefix, width=preferredWidth, subsequent_indent=2 * prefix)
    print(wrapper.fill("BITS_SENTINEL2_BQA"))
    print(wrapper.fill(str(BITS_SENTINEL2_BQA.keys())))
    print(wrapper.fill("BITS_SENTINEL2_SLC"))
    print(wrapper.fill(str(BITS_SENTINEL2_SLC.keys())))
    print(wrapper.fill("BITS_LANDSAT_BQA"))
    print(wrapper.fill(str(BITS_LANDSAT_BQA.keys())))
    print(wrapper.fill("BITS_LANDSAT_CLOUD_QA"))
    print(wrapper.fill(str(BITS_LANDSAT_CLOUD_QA.keys())))
    print(wrapper.fill("BITS_LANDSAT_PIXEL_QA"))
    print(wrapper.fill(str(BITS_LANDSAT_PIXEL_QA.keys())))
    print(wrapper.fill("BITS_LANDSAT_BQA_L8"))
    print(wrapper.fill(str(BITS_LANDSAT_BQA_L8.keys())))
    print(wrapper.fill("BITS_LANDSAT_PIXEL_QA_L8"))
    print(wrapper.fill(str(BITS_LANDSAT_PIXEL_QA_L8.keys())))


def _cloud_mask_band_naming_convention(providedOptions):
    """
    Description:

    Arguments:

    Notes:
        None.
    """
    # something like geetils_mask_bits in ascending order
    # x = sorted(a, reverse=False, key=len)
    return "geetils_mask"


def _generic_cloud_mask_band_creation(initialMaskBand, genericMaskName, operandsList, numberOfBitsList):
    """
    Description:
        Creates a custom cloud mask from the provided initial bitmask band and options.
    Arguments:
        initialMaskBand     (ee.Image)      (mandatory): The bit-mask image band.
        genericMaskName     (str)           (mandatory): self-explanatory.
        operandsList        (ee.List)       (mandatory): list of int values corresponding to provided options.
        numberOfBitsList    (ee.List)       (mandatory): list of number to shift the operands.
    Notes:
        None.
    """

    def _left_shift(index):
        return ee.Number(operandsList.get(index)).leftShift(numberOfBitsList.get(index))

    def _inner_function(current, previous):
        previous = ee.Image(previous)
        temp = ee.Image(previous.bitwiseAnd(initialMaskBand.bitwiseAnd(ee.Number(current)).eq(0)))
        return temp

    #
    sequence = ee.List.sequence(0, operandsList.size().subtract(1))

    # bitwise left shift.
    shiftedOptions = sequence.map(_left_shift)

    # mask creation.
    mask = ee.Image(shiftedOptions.iterate(_inner_function, ee.Image.constant(1)))

    # rename newly created mask.
    mask = mask.rename(genericMaskName)

    return mask


def _cloud_mask_application(mask, image, nonValue: int = None):
    """
    Description:
        Applies a cloud mask on an image.
    Arguments:
        mask    (ee.Image)  (mandatory): The cloud mask to apply upon an image.
        image   (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        nonValue    (int)   (mandatory): The value which will be applied at all positions where the input mask is zero.
    Notes:
        None.
    """
    image = image.updateMask(mask)

    if nonValue is not None:
        image = image.unmask(nonValue)

    return image


def _sentinel2_qa(image, maskName: str = None, providedOptions: list = ('cloud', 'cirrus')):
    """
    Description:
        Create a sentinel2 image cloud mask using the qa60 bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [cloud, cirrus].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_SENTINEL2_BQA.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_SENTINEL2_BQA[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("QA60"), maskName, operandsList, numberOfBitsList)


def _sentinel2_sr(image, maskName: str = None, providedOptions: list = ('high_clouds_probability', 'cirrus', 'cloud_shadows')):
    """
    Description:
        Create a sentinel2 image cloud mask using the slc bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [high_clouds_probability, cirrus, cloud_shadows].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_SENTINEL2_SCL.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_SENTINEL2_SCL[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("SCL"), maskName, operandsList, numberOfBitsList)


def _landsat457_toa(image, maskName: str = None, providedOptions: list = ('high_cloud_confidence', 'high_cloud_shadow_confidence')):
    """
    Description:
        Create a sentinel2 image cloud mask using the slc bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [high_cloud_confidence, high_cloud_shadow_confidence].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_LANDSAT_BQA.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_LANDSAT_BQA[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("BQA"), maskName, operandsList, numberOfBitsList)


def _cloud_qa_landsat457_sr(image, maskName: str = None, providedOptions: list = ('cloud', 'shadow')):
    """
    Description:
        Create a sentinel2 image cloud mask using the slc bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [cloud, shadow].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_LANDSAT_CLOUD_QA.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_LANDSAT_CLOUD_QA[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("sr_cloud_qa"), maskName, operandsList, numberOfBitsList)


def _pixel_qa_landsat457_sr(image, maskName: str = None, providedOptions: list = ('cloud', 'high_cloud_confidence', 'shadow')):
    """
    Description:
        Create a sentinel2 image cloud mask using the slc bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [cloud, high_cloud_confidence, shadow].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_LANDSAT_PIXEL_QA.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_LANDSAT_PIXEL_QA[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("pixel_qa"), maskName, operandsList, numberOfBitsList)


def _landsat8_toa(image, maskName: str = None,
                  providedOptions: list = ('high_cloud_confidence', 'high_cirrus_confidence', 'high_cloud_shadow_confidence')):
    """
    Description:
        Create a sentinel2 image cloud mask using the slc bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [high_cloud_confidence, high_cirrus_confidence, high_cloud_shadow_confidence].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_LANDSAT_BQA_L8.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_LANDSAT_BQA_L8[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("BQA"), maskName, operandsList, numberOfBitsList)


def _landsat8_sr(image, maskName: str = None, providedOptions: list = ("high_cloud_confidence", "high_cirrus_confidence")):
    """
    Description:
        Create a sentinel2 image cloud mask using the slc bitmask band.
    Arguments:
        image           (ee.Image)  (mandatory): The image on which the cloud mask will be applied.
        maskName        (str)       (mandatory): The name of the soon to be created mask.
        providedOptions (list)      (mandatory): self-explanatory. Defaults to [high_cloud_confidence, high_cirrus_confidence].
    Notes:
        None.
    """
    # remove possible duplicate values from providedOptions.
    providedOptions = set(providedOptions)

    # check that all of the providedOptions values are available.
    availableOptions = BITS_LANDSAT_PIXEL_QA_L8.keys()
    if all(option in providedOptions for option in availableOptions):
        raise ValueError("One or more of the provided options are not available. Available options are: {}".format(availableOptions))

    # create a filtered dictionary from the providedOptions.
    filteredOptions = {key: BITS_LANDSAT_PIXEL_QA_L8[key] for key in providedOptions}

    # check if no mask name was specified.
    if maskName is None:
        maskName = _cloud_mask_band_naming_convention(filteredOptions)

    # comment.
    operandsList = []
    numberOfBitsList = []
    for key, value in filteredOptions.items():
        for innerKey, innerValue in value.items():
            if "-" in innerKey:
                splitKey = innerKey.split("-")
                numberOfBits = splitKey[0]
            else:
                numberOfBits = innerKey

            operandsList.append(innerValue)
            numberOfBitsList.append(int(numberOfBits))

    operandsList = ee.List(operandsList)
    numberOfBitsList = ee.List(numberOfBitsList)
    return _generic_cloud_mask_band_creation(image.select("pixel_qa"), maskName, operandsList, numberOfBitsList)
