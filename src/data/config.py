"""
Data pipeline configuration for GeoIntelligence AI.
Centralizes paths, URLs, versioning, ISO country mappings, and feature engineering constants.
"""

from pathlib import Path
from typing import Dict, List

# Base directory resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

RAW_UCDP_DIR = DATA_DIR / "raw" / "ucdp"
PROCESSED_UCDP_DIR = DATA_DIR / "processed" / "ucdp"

# UCDP Source Configuration
UCDP_SOURCE_NAME = "Uppsala Conflict Data Program (UCDP), Uppsala University"
UCDP_DATASET_NAME = "UCDP Georeferenced Event Dataset (GED) Global"
UCDP_DATASET_VERSION = "26.1"
UCDP_DOWNLOAD_URL = "https://ucdp.uu.se/downloads/ged/ged261-csv.zip"

RAW_ZIP_FILENAME = "ged261-csv.zip"
RAW_CSV_FILENAME = "GEDEvent_v26_1.csv"
RAW_METADATA_FILENAME = "metadata.json"

PROCESSED_EVENTS_FILENAME = "ucdp_events_clean.parquet"
PROCESSED_FEATURES_FILENAME = "country_month_conflict_features.parquet"
PROCESSED_METADATA_FILENAME = "processing_metadata.json"

# Temporal Coverage for GED v26.1
MIN_YEAR = 1989
MAX_YEAR = 2025

# Feature Engineering Horizons
LAG_MONTHS: List[int] = [1, 2, 3, 6, 12]
ROLLING_WINDOWS: List[int] = [3, 6, 12]

# Project-Derived Indicator Threshold
# Note: This is an analytical operationalization for forecasting, not an official UCDP definition.
PROJECT_ACTIVE_CONFLICT_THRESHOLD = 25  # battle-related deaths in trailing 12 months

# Standard Gleditsch-Ward (GW) and country name to ISO 3166-1 alpha-3 code resolution table
GW_CODE_TO_ISO3: Dict[int, str] = {
    2: "USA", 20: "CAN", 40: "CUB", 41: "HTI", 42: "DOM", 70: "MEX",
    90: "GTM", 91: "HND", 92: "SLV", 93: "NIC", 94: "CRI", 95: "PAN",
    100: "COL", 101: "VEN", 110: "GUY", 115: "SUR", 130: "ECU", 135: "PER",
    140: "BRA", 145: "BOL", 150: "PRY", 155: "CHL", 160: "ARG", 165: "URY",
    200: "GBR", 205: "IRL", 210: "NLD", 211: "BEL", 212: "LUX", 220: "FRA",
    225: "CHE", 230: "ESP", 235: "PRT", 260: "DEU", 290: "POL", 305: "AUT",
    310: "HUN", 315: "CZE", 316: "CZE", 317: "SVK", 325: "ITA", 339: "ALB",
    341: "MNE", 343: "MKD", 344: "HRV", 345: "SRB", 346: "BIH", 347: "KOS",
    349: "SVN", 350: "GRC", 352: "CYP", 355: "BGR", 359: "MDA", 360: "ROU",
    365: "RUS", 366: "EST", 367: "LVA", 368: "LTU", 369: "UKR", 370: "BLR",
    371: "ARM", 372: "GEO", 373: "AZE", 375: "FIN", 380: "SWE", 385: "NOR",
    390: "DNK", 395: "ISL", 402: "CPV", 404: "GNB", 411: "GNQ", 420: "GMB",
    432: "MLI", 433: "SEN", 434: "BEN", 435: "MRT", 436: "NER", 437: "CIV",
    438: "GIN", 439: "BFA", 450: "LBR", 451: "SLE", 452: "GHA", 461: "TGO",
    471: "CMR", 475: "NGA", 481: "GAB", 482: "CAF", 483: "TCD", 484: "COG",
    490: "COD", 500: "UGA", 501: "KEN", 510: "TZA", 516: "BDI", 517: "RWA",
    520: "SOM", 522: "SOM", 530: "ETH", 531: "ERI", 540: "AGO", 541: "MOZ",
    551: "ZMB", 552: "ZWE", 553: "MWI", 560: "ZAF", 565: "NAM", 570: "LSO",
    571: "BWA", 572: "SWZ", 580: "MDG", 581: "COM", 590: "MUS", 600: "MAR",
    615: "DZA", 616: "TUN", 620: "LBY", 625: "SDN", 626: "SSD", 630: "IRN",
    640: "TUR", 645: "IRQ", 651: "EGY", 652: "SYR", 660: "LBN", 663: "JOR",
    666: "ISR", 670: "SAU", 678: "YEM", 680: "YEM", 690: "KWT", 692: "BHR",
    694: "QAT", 696: "ARE", 698: "OMN", 700: "AFG", 701: "TKM", 702: "TJK",
    703: "KGZ", 704: "UZB", 705: "KAZ", 710: "CHN", 712: "MNG", 713: "TWN",
    731: "PRK", 732: "KOR", 740: "JPN", 750: "IND", 760: "BTN", 770: "PAK",
    771: "BGD", 775: "MMR", 780: "LKA", 781: "MDV", 790: "NPL", 800: "THA",
    811: "KHM", 812: "LAO", 816: "VNM", 820: "MYS", 830: "SGP", 835: "BRN",
    840: "PHL", 850: "IDN", 860: "TLS", 900: "AUS", 910: "PNG", 920: "NZL",
    940: "SLB", 950: "FJI",
    51: "JAM", 52: "TTO", 338: "MLT"
}

# Country Name overrides to standard ISO 3166-1 alpha-3
COUNTRY_NAME_TO_ISO3: Dict[str, str] = {
    "Afghanistan": "AFG", "Algeria": "DZA", "Angola": "AGO", "Azerbaijan": "AZE",
    "Bangladesh": "BGD", "Burundi": "BDI", "Cambodia": "KHM", "Cameroon": "CMR",
    "Central African Republic": "CAF", "Chad": "TCD", "Colombia": "COL",
    "Congo": "COG", "DR Congo (Zaire)": "COD", "Democratic Republic of Congo": "COD",
    "Djibouti": "DJI", "Egypt": "EGY", "Eritrea": "ERI", "Ethiopia": "ETH",
    "Georgia": "GEO", "Ghana": "GHA", "Guatemala": "GTM", "Guinea": "GIN",
    "Guinea-Bissau": "GNB", "Haiti": "HTI", "India": "IND", "Indonesia": "IDN",
    "Iran": "IRN", "Iraq": "IRQ", "Israel": "ISR", "Ivory Coast": "CIV",
    "Jamaica": "JAM", "Kenya": "KEN", "Lebanon": "LBN", "Liberia": "LBR", "Libya": "LBY",
    "Mali": "MLI", "Malta": "MLT", "Mauritania": "MRT", "Mexico": "MEX", "Mozambique": "MOZ",
    "Myanmar (Burma)": "MMR", "Nepal": "NPL", "Nicaragua": "NIC", "Niger": "NER",
    "Nigeria": "NGA", "Pakistan": "PAK", "Papua New Guinea": "PNG", "Peru": "PER",
    "Philippines": "PHL", "Russia (Soviet Union)": "RUS", "Rwanda": "RWA",
    "Senegal": "SEN", "Sierra Leone": "SLE", "Somalia": "SOM", "South Africa": "ZAF",
    "South Sudan": "SSD", "Sri Lanka": "LKA", "Sudan": "SDN", "Syria": "SYR",
    "Tajikistan": "TJK", "Thailand": "THA", "Trinidad and Tobago": "TTO", "Turkey": "TUR",
    "Uganda": "UGA", "Ukraine": "UKR", "United States": "USA", "Venezuela": "VEN",
    "Yemen (North Yemen)": "YEM", "Zimbabwe": "ZWE"
}
