import ee
import textwrap


"Utilizing the static methods of Google Earth Engine's Python API this module includes functions to handle the process of an index creation."

FORMULAS = {
    "PSRI": "(Red-Blue)/Edge",
    "NORMALIZED": "(BAND1-BAND2)/(BAND1+BAND2)",
    "SAVI": "((NIR–Red)/(NIR+Red+L))*(1+L)",
    "EVI": "G * ((NIR-Red)/(NIR+C1*Red–C2*Blue+L))",
    "BSI": "((Red+SWIR)–(NIR+Blue))/((Red+SWIR)+(NIR+Blue))",
}

AVAILABLE = FORMULAS.keys()


def _available_formulas():
    """
    Description:
        Prints a helpful list of all the available indexes.
    Arguments:
         None
    Notes:
        None
    """
    prefix = "\t"
    preferredWidth = 70
    wrapper = textwrap.TextWrapper(initial_indent=prefix, width=preferredWidth, subsequent_indent=2 * prefix)
    print(wrapper.fill("NDBI (SWIR-NIR)/(SWIR+NIR)"))
    print(wrapper.fill("NDGI = (NIR - Green) / (NIR + Green)"))
    print(wrapper.fill("NDMI = (NIR – SWIR) / (NIR + SWIR)"))
    print(wrapper.fill("NBR = (NIR – SWIR) / (NIR+ SWIR)"))
    print(wrapper.fill("NDSI = (Green - SWIR) / (Green + SWIR)"))
    print(wrapper.fill("NDVI (NIR–Red)/(NIR+Red)"))
    print(wrapper.fill("GNDVI = (NIR-GREEN)/(NIR+GREEN)"))
    print(wrapper.fill("NDWI = (NIR – SWIR) / (NIR + SWIR)"))
    print(wrapper.fill("SAVI = ((NIR–Red)/(NIR+Red+L))*(1+L)"))
    print(wrapper.fill("EVI = G * ((NIR-Red)/(NIR+C1*Red–C2*Blue+L))"))
# https://giscrack.com/list-of-spectral-indices-for-sentinel-and-landsat/


def _computation(image, index: str, bands: dict, indexName: str):
    """
    Description:
        Calculates the requested index from a dictionary of bands and names it according to the given indexName.
    Arguments:
        index       (str)   (mandatory):  The name of the desired index formula.
        bands       (dict)  (mandatory):  A dictionary of bands and constants which will be used by the index's calculation formula.
        indexName   (str)   (mandatory):  The name of the index.
    Notes:
        -Argument index must be one of "PSRI", "NORMALIZED", "SAVI", "EVI", "BSI".
    """
    if index not in AVAILABLE:
        raise ValueError('Index not available. Index must be one of "PSRI", "NORMALIZED", "SAVI", "EVI", "BSI".')

    if not indexName:
        indexName = index

    formula = FORMULAS[index]

    nd = image.expression(formula, bands).rename(indexName)

    return nd


def _psri(image, red: str, blue: str, edge: str, indexName: str = "PSRI"):
    """
    Description:
        Calculates the psri index.
    Arguments:
        image       (ee.Image)  (mandatory):  The image.
        red         (str)       (mandatory):  The red band.
        blue        (str)       (mandatory):  The blue band.
        edge        (str)       (mandatory):  The edge band.
        indexName   (str)       (mandatory):  The name of the index. Defaults to PSRI.
    Notes:
        None.
    """
    return _computation(image, "PSRI", {"Red": image.select(red), "Blue": image.select(blue), "Edge": image.select(edge)}, indexName)


def _normalized_index(image, band1: str, band2: str, indexName: str):
    """
    Description:
        Calculates a normalized index.
    Arguments:
        image       (ee.Image)  (mandatory):  The image.
        band1       (str)       (mandatory):  The first band name.
        band2       (str)       (mandatory):  The second band name.
        indexName   (str)       (mandatory):  The name of the index.
    Notes:
        None.
    """
    return _computation(image, "NORMALIZED", {"BAND1": image.select(band1), "BAND2": image.select(band2)}, indexName)


def _savi(image, nir: str, red: str, L: float = 0.5, indexName: str = "SAVI"):
    """
    Description:
        Calculates the savi index.
    Arguments:
        image       (ee.Image)  (mandatory):  The image.
        nir         (str)       (mandatory):  The nir band name.
        red         (str)       (mandatory):  The red band name.
        L           (float)     (mandatory):  Canopy background adjustment factor.
        indexName   (str)       (mandatory):  The name of the index. Defaults to SAVI.
    Notes:
        None.
    """
    return _computation(image, "SAVI", {"NIR": image.select(nir), "Red": image.select(red), "L": L}, indexName)


def evi(image, nir: str, red: str, blue: str, G: float = 2.5, L: float = 1, C1: float = 6, C2: float = 7.5, indexName: str = "EVI"):
    """
    Description:
        Calculates the evi index.
    Arguments:
        image       (ee.Image)  (mandatory):  The image.
        nir         (str)       (mandatory):  The nir band name.
        red         (str)       (mandatory):  The red band name.
        blue        (str)       (mandatory):  The blue band name.
        G           (float)     (mandatory):  Gain factor.
        L           (float)     (mandatory):  Canopy background adjustment factor.
        C1          (float)     (mandatory):  First coefficient of the aerosol resistance term.
        C2          (float)     (mandatory):  Second coefficient of the aerosol resistance term.
        indexName   (str)       (mandatory):  The name of the index. Defaults to EVI.
    Notes:
        None.
    """
    return _computation(image, "EVI", {"NIR": image.select(nir), "Red": image.select(red), "Blue": image.select(blue), "G": G, "L": L, "C1": C1, "C2": C2}, indexName)


def bsi(image, nir: str, red: str, blue: str, swir: str, indexName: str = "BSI"):
    """
    Description:
        Calculates the bsi index.
    Arguments:
        image       (ee.Image)  (mandatory):  The image.
        nir         (str)       (mandatory):  The nir band name.
        red         (str)       (mandatory):  The red band name.
        blue        (str)       (mandatory):  The blue band name.
        swir        (str)       (mandatory):  The swir band name.
        indexName   (str)       (mandatory):  The name of the index. Defaults to BSI.
    Notes:
        None.
    """
    return _computation(image, "BSI", {"NIR": image.select(nir), "Red": image.select(red), "Blue": image.select(blue), "SWIR": image.select(swir)}, indexName)
