class MissingManifestError(Exception):
    """Raise when input manifest not found"""

class InvalidRowError(Exception):
    """Raise when manifest row have invalid structure"""

class EmptyManifestError(Exception):
    """Raise when manifest have no data record"""