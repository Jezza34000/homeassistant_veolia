"""Constants for veolia."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

DOMAIN = "veolia"
NAME = "Veolia"
CONF_PORTAL_URL = "portal_url"
COMMUNE_LOOKUP_URL = (
    "https://prd-ael-sirius-refcommunes.istefr.fr/communes-nationales?q="
)

# Platforms
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.TEXT, Platform.BINARY_SENSOR]

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
