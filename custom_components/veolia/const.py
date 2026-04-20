"""Constants for veolia."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "veolia"
NAME = "Veolia"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

# API constants keys
LAST_DATA = -1
IDX = "index"
LITRE = "litre"
CUBIC_METER = "m3"
CONSO = "consommation"
IDX_FIABILITY = "fiabilite_index"
CONSO_FIABILITY = "fiabilite_conso"
DATA_DATE = "date_releve"
YEAR = "annee"
MONTH = "mois"
