"""
Configuration constants and reference mappings for Country Relationship Network.
Centralizes paths, empirical mapping dictionaries, network parameters, and tension index weights.
"""

from pathlib import Path
from typing import Dict, List, Set

# Base directory resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Input paths (Member 3 processed datasets)
PROCESSED_UCDP_DIR = DATA_DIR / "processed" / "ucdp"
UCDP_EVENTS_PATH = PROCESSED_UCDP_DIR / "ucdp_events_clean.parquet"
UCDP_FEATURES_PATH = PROCESSED_UCDP_DIR / "country_month_conflict_features.parquet"

PROCESSED_NEWS_DIR = DATA_DIR / "processed" / "news"
NEWS_ARTICLES_PATH = PROCESSED_NEWS_DIR / "news_articles_clean.parquet"
NEWS_FEATURES_PATH = PROCESSED_NEWS_DIR / "country_month_news_features.parquet"

# Output paths
PROCESSED_RELATIONSHIPS_DIR = DATA_DIR / "processed" / "relationships"
OUTPUT_DYADS_FILENAME = "country_dyad_relationships.parquet"
OUTPUT_METRICS_FILENAME = "country_network_metrics.parquet"
OUTPUT_GRAPH_JSON_FILENAME = "network_graph.json"
OUTPUT_METADATA_FILENAME = "processing_metadata.json"

OUTPUT_DYADS_PATH = PROCESSED_RELATIONSHIPS_DIR / OUTPUT_DYADS_FILENAME
OUTPUT_METRICS_PATH = PROCESSED_RELATIONSHIPS_DIR / OUTPUT_METRICS_FILENAME
OUTPUT_GRAPH_JSON_PATH = PROCESSED_RELATIONSHIPS_DIR / OUTPUT_GRAPH_JSON_FILENAME
OUTPUT_METADATA_PATH = PROCESSED_RELATIONSHIPS_DIR / OUTPUT_METADATA_FILENAME

# Graph algorithm parameters
PAGERANK_ALPHA: float = 0.85
PAGERANK_MAX_ITER: int = 100
PAGERANK_TOL: float = 1e-6

# Forecasting Lag Horizons
LAG_MONTHS: List[int] = [1, 2, 3, 6, 12]
ROLLING_WINDOWS: List[int] = [3, 6, 12]

# Analytical Composite Tension Index Parameters
# Note: This is an analytical project-derived metric, not an official UCDP/GDELT definition.
TENSION_WEIGHT_CONFLICT: float = 0.6
TENSION_WEIGHT_NEWS: float = 0.4
FATALITIES_LOG_SCALE: float = 1000.0  # Log normalizer for fatalities

# Comprehensive UCDP Government entity name to ISO 3166-1 alpha-3 code resolution
# Maps "Government of <Entity>" values observed in UCDP GED 26.1
UCDP_GOV_NAME_TO_ISO3: Dict[str, str] = {
    "Afghanistan": "AFG",
    "Algeria": "DZA",
    "Angola": "AGO",
    "Australia": "AUS",
    "Azerbaijan": "AZE",
    "Bahrain": "BHR",
    "Bangladesh": "BGD",
    "Benin": "BEN",
    "Bosnia-Herzegovina": "BIH",
    "Brazil": "BRA",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cambodia (Kampuchea)": "KHM",
    "Cambodia": "KHM",
    "Cameroon": "CMR",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "China": "CHN",
    "Colombia": "COL",
    "Comoros": "COM",
    "Congo": "COG",
    "Croatia": "HRV",
    "DR Congo (Zaire)": "COD",
    "Democratic Republic of Congo": "COD",
    "Djibouti": "DJI",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "El Salvador": "SLV",
    "Eritrea": "ERI",
    "Ethiopia": "ETH",
    "Gambia": "GMB",
    "Georgia": "GEO",
    "Ghana": "GHA",
    "Guatemala": "GTM",
    "Guinea": "GIN",
    "Guinea-Bissau": "GNB",
    "Haiti": "HTI",
    "India": "IND",
    "Indonesia": "IDN",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Israel": "ISR",
    "Ivory Coast": "CIV",
    "Jamaica": "JAM",
    "Jordan": "JOR",
    "Kenya": "KEN",
    "Kuwait": "KWT",
    "Kyrgyzstan": "KGZ",
    "Laos": "LAO",
    "Lebanon": "LBN",
    "Lesotho": "LSO",
    "Liberia": "LBR",
    "Libya": "LBY",
    "Madagascar": "MDG",
    "Malaysia": "MYS",
    "Mali": "MLI",
    "Malta": "MLT",
    "Mauritania": "MRT",
    "Mexico": "MEX",
    "Moldova": "MDA",
    "Morocco": "MAR",
    "Mozambique": "MOZ",
    "Myanmar (Burma)": "MMR",
    "Nepal": "NPL",
    "Nicaragua": "NIC",
    "Niger": "NER",
    "Nigeria": "NGA",
    "North Macedonia": "MKD",
    "Pakistan": "PAK",
    "Panama": "PAN",
    "Papua New Guinea": "PNG",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Philippines": "PHL",
    "Romania": "ROU",
    "Russia (Soviet Union)": "RUS",
    "Rwanda": "RWA",
    "Senegal": "SEN",
    "Serbia (Yugoslavia)": "SRB",
    "Sierra Leone": "SLE",
    "Somalia": "SOM",
    "South Africa": "ZAF",
    "South Sudan": "SSD",
    "Spain": "ESP",
    "Sri Lanka": "LKA",
    "Sudan": "SDN",
    "Syria": "SYR",
    "Tajikistan": "TJK",
    "Tanzania": "TZA",
    "Thailand": "THA",
    "Togo": "TGO",
    "Trinidad and Tobago": "TTO",
    "Tunisia": "TUN",
    "Turkey": "TUR",
    "Uganda": "UGA",
    "Ukraine": "UKR",
    "United Kingdom": "GBR",
    "United States": "USA",
    "United States of America": "USA",
    "Uzbekistan": "UZB",
    "Venezuela": "VEN",
    "Yemen (North Yemen)": "YEM",
    "Zimbabwe": "ZWE",
    "Zimbabwe (Rhodesia)": "ZWE",
    "eSwatini (Swaziland)": "SWZ",
}

# Standard English Names for the 125 Reference Countries
ISO3_TO_COUNTRY_NAME: Dict[str, str] = {
    "AFG": "Afghanistan", "AGO": "Angola", "ALB": "Albania", "ARE": "United Arab Emirates",
    "ARG": "Argentina", "ARM": "Armenia", "AUS": "Australia", "AUT": "Austria",
    "AZE": "Azerbaijan", "BDI": "Burundi", "BEL": "Belgium", "BEN": "Benin",
    "BFA": "Burkina Faso", "BGD": "Bangladesh", "BHR": "Bahrain", "BIH": "Bosnia and Herzegovina",
    "BLR": "Belarus", "BOL": "Bolivia", "BRA": "Brazil", "BRN": "Brunei",
    "BTN": "Bhutan", "BWA": "Botswana", "CAF": "Central African Republic", "CAN": "Canada",
    "CHE": "Switzerland", "CHL": "Chile", "CHN": "China", "CIV": "Ivory Coast",
    "CMR": "Cameroon", "COD": "Democratic Republic of the Congo", "COG": "Republic of the Congo",
    "COL": "Colombia", "COM": "Comoros", "CPV": "Cape Verde", "CRI": "Costa Rica",
    "CUB": "Cuba", "CYP": "Cyprus", "CZE": "Czech Republic", "DEU": "Germany",
    "DJI": "Djibouti", "DNK": "Denmark", "DOM": "Dominican Republic", "DZA": "Algeria",
    "ECU": "Ecuador", "EGY": "Egypt", "ERI": "Eritrea", "ESP": "Spain",
    "EST": "Estonia", "ETH": "Ethiopia", "FIN": "Finland", "FJI": "Fiji",
    "FRA": "France", "GAB": "Gabon", "GBR": "United Kingdom", "GEO": "Georgia",
    "GHA": "Ghana", "GIN": "Guinea", "GMB": "Gambia", "GNB": "Guinea-Bissau",
    "GNQ": "Equatorial Guinea", "GRC": "Greece", "GTM": "Guatemala", "GUY": "Guyana",
    "HND": "Honduras", "HRV": "Croatia", "HTI": "Haiti", "HUN": "Hungary",
    "IDN": "Indonesia", "IND": "India", "IRL": "Ireland", "IRN": "Iran",
    "IRQ": "Iraq", "ISL": "Iceland", "ISR": "Israel", "ITA": "Italy",
    "JAM": "Jamaica", "JOR": "Jordan", "JPN": "Japan", "KAZ": "Kazakhstan",
    "KEN": "Kenya", "KGZ": "Kyrgyzstan", "KHM": "Cambodia", "KOR": "South Korea",
    "KOS": "Kosovo", "KWT": "Kuwait", "LAO": "Laos", "LBN": "Lebanon",
    "LBR": "Liberia", "LBY": "Libya", "LKA": "Sri Lanka", "LSO": "Lesotho",
    "LTU": "Lithuania", "LUX": "Luxembourg", "LVA": "Latvia", "MAR": "Morocco",
    "MDA": "Moldova", "MDG": "Madagascar", "MDV": "Maldives", "MEX": "Mexico",
    "MKD": "North Macedonia", "MLI": "Mali", "MLT": "Malta", "MMR": "Myanmar",
    "MNE": "Montenegro", "MNG": "Mongolia", "MOZ": "Mozambique", "MRT": "Mauritania",
    "MUS": "Mauritius", "MWI": "Malawi", "MYS": "Malaysia", "NAM": "Namibia",
    "NER": "Niger", "NGA": "Nigeria", "NIC": "Nicaragua", "NLD": "Netherlands",
    "NOR": "Norway", "NPL": "Nepal", "NZL": "New Zealand", "OMN": "Oman",
    "PAK": "Pakistan", "PAN": "Panama", "PER": "Peru", "PHL": "Philippines",
    "PNG": "Papua New Guinea", "POL": "Poland", "PRK": "North Korea", "PRT": "Portugal",
    "PRY": "Paraguay", "QAT": "Qatar", "ROU": "Romania", "RUS": "Russia",
    "RWA": "Rwanda", "SAU": "Saudi Arabia", "SDN": "Sudan", "SEN": "Senegal",
    "SGP": "Singapore", "SLB": "Solomon Islands", "SLE": "Sierra Leone", "SLV": "El Salvador",
    "SOM": "Somalia", "SRB": "Serbia", "SSD": "South Sudan", "SUR": "Suriname",
    "SVK": "Slovakia", "SVN": "Slovenia", "SWE": "Sweden", "SWZ": "Eswatini",
    "SYR": "Syria", "TCD": "Chad", "TGO": "Togo", "THA": "Thailand",
    "TJK": "Tajikistan", "TKM": "Turkmenistan", "TLS": "Timor-Leste", "TTO": "Trinidad and Tobago",
    "TUN": "Tunisia", "TUR": "Turkey", "TWN": "Taiwan", "TZA": "Tanzania",
    "UGA": "Uganda", "UKR": "Ukraine", "USA": "United States", "URY": "Uruguay",
    "UZB": "Uzbekistan", "VEN": "Venezuela", "VNM": "Vietnam", "YEM": "Yemen",
    "ZAF": "South Africa", "ZMB": "Zambia", "ZWE": "Zimbabwe"
}
