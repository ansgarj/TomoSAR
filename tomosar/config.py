from pathlib import Path
import json

# Project and package paths
PACKAGE_PATH = Path(__file__).resolve().parent
PROJECT_PATH = PACKAGE_PATH.parent
LOCAL = PROJECT_PATH / ".local"
SETTINGS_PATH = LOCAL / "settings.json"

# Frequency parameters
class Frequencies:
    __slots__ = ('BANDS', 'BANDWIDTHS', 'CENTRAL_FREQUENCIES', 'UNIT')

    def __init__(self):
        st = Settings()
        object.__setattr__(self, "BANDS", tuple(
            st.RADAR["POLARIZATIONS"].keys()
        ))
        object.__setattr__(self, "BANDWIDTHS", tuple(
            st.RADAR["BANDWIDTHS"][band] for band in self.BANDS
        ))
        object.__setattr__(self, "CENTRAL_FREQUENCIES", tuple(
            st.RADAR["CENTRAL_FREQUENCIES"][band] for band in self.BANDS
        ))
        object.__setattr__(self, "UNIT", "Hz")

    def __setattr__(self, key, value) -> None:
        raise AttributeError(f"{self.__class__.__name__} is immutable")

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

# Beam parameters
class Beam:
    __slots__ = ("BAND_POLARIZATIONS", "BEAMWIDTHS", "DEPRESSION_ANGLES", "UNIT")

    def __init__(self):
        st = Settings()
        object.__setattr__(self, "BAND_POLARIZATIONS", tuple(
            (band, pol) for band, pol_list in st.RADAR["POLARIZATIONS"].items() for pol in pol_list
        ))
        object.__setattr__(self, "BEAMWIDTHS", tuple(
            st.RADAR["BEAMWIDTHS"][band][pol] for band, pol in self.BAND_POLARIZATIONS
        ))
        object.__setattr__(self, "DEPRESSION_ANGLES", tuple(
            st.RADAR["DEPRESSION_ANGLES"][band][pol] for band, pol in self.BAND_POLARIZATIONS
        ))
        object.__setattr__(self, "UNIT", "deg")

    def get(self, key: str, band: str = "", pol = "") -> float|None:
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
    
    def zip(self, attributes: list[str]|tuple[str, ...] = []):
        if not (isinstance(attributes, list) or isinstance(attributes, tuple)):
            raise TypeError
        if not attributes:
            return zip(self.BAND_POLARIZATIONS, self.BEAMWIDTHS, self.DEPRESSION_ANGLES)
        values = []
        for attr in attributes:
            values.append(self.get(attr))
        return zip(*values)

# Settings
class Settings:
    def __init__(self):
        if SETTINGS_PATH.exists() and SETTINGS_PATH.is_file():
            with open(SETTINGS_PATH, "r") as file:
                self.data = json.load(file)
        else:
            save_default()
            self.data = DEFAULT

    @property
    def VERBOSE(self):
        return self.data["VERBOSE"]
    
    @property
    def MOCOREF_LONGITUDE(self):
        return self.data["MOCOREF_LONGITUDE"]
    
    @property
    def MOCOREF_LATITUDE(self):
        return self.data["MOCOREF_LATITUDE"]
    
    @property
    def MOCOREF_HEIGHT(self):
        return self.data["MOCOREF_HEIGHT"]
    
    @property
    def MOCOREF_ANTENNA(self):
        return self.data["MOCOREF_ANTENNA"]
    
    @property
    def RTKP_CONFIG(self):
        return self.data["RTKP_CONFIG"]
    
    @property
    def DATA_DIRS(self) -> Path:
        dirs = self.data["DATA_DIRS"]
        dirs.mkdir(parents=True, exist_ok=True)
        return dirs
    
    @property
    def PROCESSING_DIRS(self) -> Path:
        dirs = self.data["PROCESSING_DIRS"]
        dirs.mkdir(parents=True, exist_ok=True)
        return dirs
    
    @property
    def TOMO_DIRS(self) -> Path:
        dirs = self.data["TOMO_DIRS"]
        dirs.mkdir(parents=True, exist_ok=True)
        return dirs
    
    @property
    def SWEPOS_LOGIN(self):
        return self.data["SWEPOS_LOGIN"]
    
    @property
    def SWEPOS_USERNAME(self):
        return self.SWEPOS_LOGIN["USERNAME"]
    
    @property
    def SWEPOS_PASSWORD(self):
        return self.SWEPOS_LOGIN["PASSWORD"]
    
    @property
    def DEFAULT_POC(self):
        return self.data["DEFAULT_POC"]
    
    @property
    def FILES(self):
        return self.data["FILES"]
    
    @property
    def DEMS(self):
        return self.FILES["DEMS"]
    
    @property
    def CANOPIES(self):
        return self.FILES["CANOPIES"]
    
    @property
    def MASKS(self):
        return self.FILES["MASKS"]
    
    @property
    def ANTENNAS(self):
        return self.FILES["ANTENNAS"]
    
    @property
    def SATELLITES(self):
        return self.ANTENNAS.get("SATELLITES", None)
    
    @property
    def RECEIVERS(self):
        return {key: value for key, value in self.ANTENNAS.items() if key != "SATELLITES"}
    
    def RECEIVER(self, receiver_id: str, radome: str = None):
        if radome:
            return self.RECEIVERS.get(receiver_id,{}).get(radome, None)
        else:
            return self.RECEIVERS.get(receiver_id, {})
        
    @property
    def RADAR(self):
        return self.data["RADAR"]
    
    def __setattr__(self, key: str, value) -> None:
        if key == "data":
            super().__setattr__(key, value)
        elif key == "SWEPOS_USERNAME":
            self.data["SWEPOS_LOGIN"]["USERNAME"] = value
        elif key == "SWEPOS_PASSWORD":
            self.data["SWEPOS_LOGIN"]["PASSWORD"] = value
        elif key == "DEMS":
            self.data["FILES"]["DEMS"] = value
        elif key == "CANOPIES":
            self.data["FILES"]["CANOPIES"] = value
        elif key == "MASKS":
            self.data["FILES"]["MASKS"] = value
        elif key == "SATELLITES":
            self.data["FILES"]["ANTENNAS"]["SATELLITES"] = value
        elif key == "RECEIVERS":
            antennas = [self.SATELLITES]
            self.data["FILES"]["ANTENNAS"] = antennas.extend(value)
        else:
            self.data[key] = value

    def print(self) -> None:
        print(json.dumps(self.data, indent=4))

    def save(self) -> None:
        LOCAL.mkdir(exist_ok=True)
        with open(SETTINGS_PATH, "w") as file:
            json.dump(self.data, file, indent=4)

    def reset(self) -> None:
        self.data = DEFAULT

DEFAULT = {
    "VERBOSE": False,
    "MOCOREF_LONGITUDE": "Longitude",
    "MOCOREF_LATITUDE": "Latitude",
    "MOCOREF_HEIGHT": "Ellipsoidal height",
    "MOCOREF_ANTENNA": "Antenna height",
    "RTKP_CONFIG": None,
    "DATA_DIRS": str(Path.home() / "Radar" / "Data"),
    "PROCESSING_DIRS": str(Path.home() / "Radar" / "Processing"),
    "TOMO_DIRS": str(Path.home() / "Radar" / "Tomograms"),
    "SWEPOS_LOGIN": {
        "USERNAME": None,
        "PASSWORD": None
    },
    "DEFAULT_POC": {
        1: [0, 0, 0.9],
        2: [0, 0, 0.9],
        3: [0, 0, 0.9],
        4: [0, 0, 0.9],
        5: [0, 0, 0.9],
    },
    "FILES": {
        "ANTENNAS": {
            "SATELLITES": None
        },
        "DEMS": [],
        "CANOPIES": [],
        "MASKS": []
    },
    "RADAR": {
        "POLARIZATIONS": {
            "P-band": ["H-pol"],
            "L-band": ["H-pol", "V-pol"],
            "C-band": ["V-pol"]
        },
        "CENTRAL_FREQUENCIES": {
            "P-band": 412.5e6,
            "L-band": 1.25e9,
            "C-band": 5.3125e9,
        },
        "BANDWIDTHS": {
            "P-band": 25e6,
            "L-band": 50e6,
            "C-band": 125e6
        },
        "BEAMWIDTHS": {
            "P-band": {
                "H-pol": 75.2,
                "V-pol": None,
            },
            "L-band": {
                "H-pol": 78.7,
                "V-pol": 58.8,
            },
            "C-band": {
                "H-pol": None,
                "V-pol": 51.3
            } 
        },
        "DEPRESSION_ANGLES": {
            "P-band": {
                "H-pol": 45.,
                "V-pol": None,
            },
            "L-band": {
                "H-pol": 45.,
                "V-pol": 45.,
            },
            "C-band": {
                "H-pol": None,
                "V-pol": 45.
            } 
        },
    }
}

def save_default() -> None:
    LOCAL.mkdir(exist_ok=True)
    with open(SETTINGS_PATH, "w") as file:
        json.dump(DEFAULT, file, indent=4)