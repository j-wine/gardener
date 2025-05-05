from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

Base = declarative_base()


class Plant(Base):
    __tablename__ = "plants"

    # Index for each crop
    EcoPortCode = Column(Integer, primary_key=True, index=True, nullable=False)

    # The scientific (Latin) name of the plant species.
    ScientificName = Column(String, nullable=False, index=True)

    # The author or authority who described the species scientifically.
    AUTH = Column(String, nullable=True)

    # The botanical family to which the species belongs.
    FAMNAME = Column(String, nullable=True)

    # Synonyms or alternative scientific names that the species may have been known by in different taxonomic references.
    SYNO = Column(String, nullable=True)

    # Common names of the species in various languages or regions.
    COMNAME = Column(String, nullable=True)

    # Life form, indicating whether the plant is a herb, shrub, tree, etc.
    LIFO = Column(String, nullable=True)

    # Habitat where the plant is typically found or grows naturally.
    HABI = Column(String, nullable=True)

    # Life span of the species, indicating whether it is annual, biennial, perennial, etc.
    LISPA = Column(String, nullable=True)

    # Physical structure or morphology of the plant, e.g., single stem, multi-stem, erect, etc.
    PHYS = Column(String, nullable=True)

    # The category or use of the plant, such as vegetables, fruits, nuts, ornamentals, etc.
    CAT = Column(String, nullable=True)

    # Plant attributes, such as whether it is deciduous, evergreen, etc.
    PLAT = Column(String, nullable=True)

    # Optimal minimum temperature for the growth of the plant (in degrees Celsius).
    TOPMN = Column(Float, nullable=False)

    # Optimal maximum temperature for the growth of the plant (in degrees Celsius).
    TOPMX = Column(Float, nullable=False)

    # Absolute minimum temperature the plant can tolerate (in degrees Celsius).
    TMIN = Column(Float, nullable=False)

    # Absolute maximum temperature the plant can tolerate (in degrees Celsius).
    TMAX = Column(Float, nullable=False)

    # Optimal minimum rainfall (in mm/year) required for the plant's growth.
    ROPMN = Column(Float, nullable=False)

    # Optimal maximum rainfall (in mm/year) suitable for the plant.
    ROPMX = Column(Float, nullable=False)

    # Absolute minimum rainfall (in mm/year) the plant can survive.
    RMIN = Column(Float, nullable=False)

    # Absolute maximum rainfall (in mm/year) the plant can endure.
    RMAX = Column(Float, nullable=False)

    # Absolute killing temperature where the plant dies.
    KTMP = Column(Float, nullable=False)

    # Minimum growing cycle length (in days) required for the plant to complete its life cycle.
    GMIN = Column(Float, nullable=False)

    # Maximum growing cycle length (in days) that the plant can sustain.
    GMAX = Column(Float, nullable=False)

    # Optimal minimum latitude where the plant can grow.
    LATOPMN = Column(Float, nullable=True)

    # Optimal maximum latitude where the plant can grow.
    LATOPMX = Column(Float, nullable=True)

    # Absolute minimum latitude where the plant can survive.
    LATMN = Column(Float, nullable=True)

    # Absolute maximum latitude where the plant can survive.
    LATMX = Column(Float, nullable=True)

    # Maximum altitude (in meters above sea level) where the plant can grow.
    ALTMX = Column(Float, nullable=True)

    # Optimal minimum light intensity (possibly in lumens) required for the plant's growth.
    LIOPMN = Column(String, nullable=True)

    # Optimal maximum light intensity suitable for the plant.
    LIOPMX = Column(String, nullable=True)

    # Absolute minimum light intensity the plant can tolerate.
    LIMN = Column(String, nullable=True)

    # Absolute maximum light intensity the plant can tolerate.
    LIMX = Column(String, nullable=True)

    # Optimal soil depth (in cm) required for the plant's root system.
    DEP = Column(String, nullable=True)

    # Range of soil depth suitable for the plant.
    DEPR = Column(String, nullable=True)

    # Soil texture preference of the plant, such as heavy, medium, light, or organic.
    TEXT = Column(String, nullable=True)

    # Range of soil textures the plant can tolerate.
    TEXTR = Column(String, nullable=True)

    # Fertility requirement for the plant to grow optimally.
    FER = Column(String, nullable=True)

    # Fertility range that the plant can tolerate.
    FERR = Column(String, nullable=True)

    # Toxicity levels that the plant can tolerate.
    TOX = Column(String, nullable=True)

    # Range of toxicity levels tolerable by the plant.
    TOXR = Column(String, nullable=True)

    # Salinity levels suitable for the plant's growth.
    SAL = Column(String, nullable=True)

    # Range of salinity levels the plant can tolerate.
    SALR = Column(String, nullable=True)

    # Drainage preference for the soil where the plant grows.
    DRA = Column(String, nullable=True)

    # Range of drainage conditions tolerable by the plant.
    DRAR = Column(String, nullable=True)

    # killing temperature range for the plant.
    KTMPR = Column(Float, nullable=True)

    # Photoperiod requirement, such as short day (<12 hours), neutral day (12-14 hours), long day (>14 hours).
    PHOTO = Column(String, nullable=True)

    # Climatic zone or conditions where the plant grows optimally.
    CLIZ = Column(String, nullable=True)

    # Additional biotic tolerance levels, such as pest resistance.
    ABITOL = Column(String, nullable=True)

    # Additional biotic susceptibility, indicating specific pests or diseases the plant is vulnerable to.
    ABISUS = Column(String, nullable=True)

    # Intraspecific relationships, possibly indicating whether the plant is self-compatible, dioecious, etc.
    INTRI = Column(String, nullable=True)

    # Propagation system or method, indicating how the plant is propagated.
    PROSY = Column(String, nullable=True)


class PlantModel(BaseModel):
    EcoPortCode: int
    ScientificName: str
    AUTH: Optional[str]
    FAMNAME: Optional[str]
    SYNO: Optional[str]
    COMNAME: Optional[str]
    LIFO: Optional[str]
    HABI: Optional[str]
    LISPA: Optional[str]
    PHYS: Optional[str]
    CAT: Optional[str]
    PLAT: Optional[str]
    TOPMN: float
    TOPMX: float
    TMIN: float
    TMAX: float
    ROPMN: float
    ROPMX: float
    RMIN: float
    RMAX: float
    KTMP: float
    GMIN: float
    GMAX: float
    LATOPMN: Optional[float] = None
    LATOPMX: Optional[float] = None
    LATMN: Optional[float] = None
    LATMX: Optional[float] = None
    ALTMX: Optional[float] = None
    LIOPMN: Optional[str] = None
    LIOPMX: Optional[str] = None
    LIMN: Optional[str] = None
    LIMX: Optional[str] = None
    DEP: Optional[str] = None
    DEPR: Optional[str] = None
    TEXT: Optional[str] = None
    TEXTR: Optional[str] = None
    FER: Optional[str] = None
    FERR: Optional[str] = None
    TOX: Optional[str] = None
    TOXR: Optional[str] = None
    SAL: Optional[str] = None
    SALR: Optional[str] = None
    DRA: Optional[str] = None
    DRAR: Optional[str] = None
    KTMPR: Optional[float] = None
    PHOTO: Optional[str] = None
    CLIZ: Optional[str] = None
    ABITOL: Optional[str] = None
    ABISUS: Optional[str] = None
    INTRI: Optional[str] = None
    PROSY: Optional[str] = None

    class Config:
        from_attributes = True


class SuitabilityDetails(BaseModel):
    suitability_score: float
    interval_used: int


class WeatherData(BaseModel):
    temperature_2m_mean: Optional[List[float]] = None
    precipitation_sum: Optional[List[float]] = None


class PlantSuitabilityResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    plant_name: str
    suitability_details: SuitabilityDetails
    weather_data: WeatherData

    class Config:
        from_attributes = True
