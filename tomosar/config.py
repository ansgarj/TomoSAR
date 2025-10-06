import numpy as np
from dataclasses import dataclass, field

# Depression angle for all antennas
DEPRESSION_ANGLE = 45. # degrees (for all bands)

# Bandwidths and central frequencies for C, L, and P bands
@dataclass(frozen=True)
class Frequencies:
    BANDS: tuple[str, str, str] = ('C-band', 'L-band', 'P-band')
    BANDWIDTHS: tuple = field(default_factory=lambda: np.array([125e6, 50e6, 25e6]) * 0.4) # (approximate bandwidth after range compression)
    CENTRAL_FREQUENCIES: tuple = field(default_factory=lambda: np.array([5.3125e9, 1.25e9, 412.5e6])) #
    UNIT: str = 'Hz'

    def get(self, key: str, band: str = ""):
        if band:
            if band == "C":
                band = "C-band"
            if band == "L":
                band = "L-band"
            if band == "P":
                band = "P-band"
            value = getattr(self, key, None)
            for i, b in enumerate(self.BANDS):
                if b == band:
                    return value[i]
        else:
            return getattr(self, key, None)

    def zip(self, attributes: list[str]|tuple[str, ...] = []):
        if not (isinstance(attributes, list) or isinstance(attributes, tuple)):
            raise TypeError
        if not attributes:
            return zip(self.BANDS, self.BANDWIDTHS, self.CENTRAL_FREQUENCIES)
        values = []
        for attr in attributes:
            values.append(self.get(attr))
        return zip(*values)

# Beam width for CV, LV, LH and PH antennas
@dataclass(frozen=True)
class Beam:
    BAND_POLARIZATIONS: tuple[tuple[str,str], tuple[str,str], tuple[str,str], tuple[str,str]] = (
        ('C-band','V-pol'), ('L-band', 'V-pol'), ('L-band', 'H-pol'), ('P-band', 'H-pol')
    )
    BEAMWIDTHS: tuple = field(default_factory=lambda: np.array([51.3, 58.8, 78.7, 75.2]))
    UNIT: str = 'deg'

    def get(self, key: str, band: str = "", pol = ""):
        if band and pol:
            if band in ["C", "c"]:
                band = "C-band"
            if band in ["L", "l"]:
                band = "L-band"
            if band in ["P", "p"]:
                band = "P-band"
            if pol in ["V", "v"]:
                pol = "V-pol"
            if pol in ["H", "h"]:
                pol = "H-pol"
            value = getattr(self, key, None)
            for i, (b, p) in enumerate(self.BAND_POLARIZATIONS):
                if b == band and p == pol:
                    return value[i] if value is not None else None         
        else:
            return getattr(self, key, None)
    
    def zip(self):
        return zip(self.BAND_POLARIZATIONS, self.BEAMWIDTHS)
