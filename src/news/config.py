"""
Configuration constants for News Intelligence & NLP Pipeline (GDELT DOC 2.0).
Defines paths, API endpoints, rate-limiting parameters, country entity lexicons,
9-category conflict taxonomy, and deterministic sentiment lexicons.
"""

from pathlib import Path
from typing import Dict, List, Set

# Base directory paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

RAW_NEWS_DIR = DATA_DIR / "raw" / "news" / "gdelt"
PROCESSED_NEWS_DIR = DATA_DIR / "processed" / "news"

# UCDP Processed dataset reference for downstream validation and joinability
UCDP_PROCESSED_FEATURES_PATH = (
    DATA_DIR / "processed" / "ucdp" / "country_month_conflict_features.parquet"
)

# GDELT DOC 2.0 API Configuration
GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_API_USER_AGENT = "GeoIntelligence-AI-Pipeline/1.0"
GDELT_RATE_LIMIT_PAUSE_SECONDS = 6.0  # GDELT enforces 1 request per 5 seconds minimum
GDELT_BACKOFF_RETRIES = 3
GDELT_TIMEOUT_SECONDS = 25

RAW_ARTICLES_FILENAME = "raw_articles.json"
RAW_METADATA_FILENAME = "metadata.json"
PROCESSED_ARTICLES_FILENAME = "news_articles_clean.parquet"
PROCESSED_FEATURES_FILENAME = "country_month_news_features.parquet"
PROCESSED_METADATA_FILENAME = "processing_metadata.json"

# Forecasting Lag and Rolling Window Settings (strict prior-only for leak-free forecasting)
LAG_MONTHS: List[int] = [1, 2, 3, 6, 12]
ROLLING_WINDOWS: List[int] = [3, 6, 12]

# Verified raw fields returned by GDELT DOC 2.0 API in artlist mode:
# 'url', 'url_mobile', 'title', 'seendate', 'socialimage', 'domain', 'language', 'sourcecountry'
GDELT_RAW_FIELDS = [
    "url",
    "url_mobile",
    "title",
    "seendate",
    "socialimage",
    "domain",
    "language",
    "sourcecountry",
]

# Gazetteers: Country Demonyms and Entities to ISO 3166-1 alpha-3
# Decouples source publication country from target mentioned entity
ENTITY_TO_ISO3: Dict[str, str] = {
    # High-profile active conflict zones and geopolitical actors
    "ukraine": "UKR", "ukrainian": "UKR", "kyiv": "UKR", "kiev": "UKR",
    "russia": "RUS", "russian": "RUS", "moscow": "RUS", "kremlin": "RUS",
    "sudan": "SDN", "sudanese": "SDN", "khartoum": "SDN", "darfur": "SDN",
    "south sudan": "SSD", "juba": "SSD",
    "israel": "ISR", "israeli": "ISR", "jerusalem": "ISR", "tel aviv": "ISR",
    "palestine": "PSE", "palestinian": "PSE", "gaza": "PSE", "west bank": "PSE",
    "syria": "SYR", "syrian": "SYR", "damascus": "SYR", "aleppo": "SYR",
    "yemen": "YEM", "yemeni": "YEM", "sanaa": "YEM", "houthi": "YEM",
    "lebanon": "LBN", "lebanese": "LBN", "beirut": "LBN", "hezbollah": "LBN",
    "iran": "IRN", "iranian": "IRN", "tehran": "IRN",
    "iraq": "IRQ", "iraqi": "IRQ", "baghdad": "IRQ",
    "somalia": "SOM", "somali": "SOM", "mogadishu": "SOM", "al-shabaab": "SOM",
    "congo": "COD", "drc": "COD", "kinshasa": "COD",
    "nigeria": "NGA", "nigerian": "NGA", "abuja": "NGA", "boko haram": "NGA",
    "mali": "MLI", "malian": "MLI", "bamako": "MLI",
    "burkina faso": "BFA", "ouagadougou": "BFA",
    "niger": "NER", "niamey": "NER",
    "ethiopia": "ETH", "ethiopian": "ETH", "addis ababa": "ETH", "tigray": "ETH",
    "afghanistan": "AFG", "afghan": "AFG", "kabul": "AFG", "taliban": "AFG",
    "pakistan": "PAK", "pakistani": "PAK", "islamabad": "PAK",
    "india": "IND", "indian": "IND", "new delhi": "IND", "kashmir": "IND",
    "china": "CHN", "chinese": "CHN", "beijing": "CHN",
    "taiwan": "TWN", "taiwanese": "TWN", "taipei": "TWN",
    "myanmar": "MMR", "burma": "MMR", "burmese": "MMR", "yangon": "MMR", "naypyidaw": "MMR",
    "colombia": "COL", "colombian": "COL", "bogota": "COL",
    "mexico": "MEX", "mexican": "MEX", "mexico city": "MEX",
    "haiti": "HTI", "haitian": "HTI", "port-au-prince": "HTI",
    "armenia": "ARM", "armenian": "ARM", "yerevan": "ARM",
    "azerbaijan": "AZE", "azerbaijani": "AZE", "baku": "AZE", "nagorno-karabakh": "AZE",
    "united states": "USA", "us": "USA", "american": "USA", "washington": "USA", "pentagon": "USA",
}

# Standard GDELT Sourcecountry names to ISO-3 mapping
GDELT_SOURCE_COUNTRY_TO_ISO3: Dict[str, str] = {
    "united states": "USA", "united kingdom": "GBR", "russia": "RUS",
    "china": "CHN", "france": "FRA", "germany": "DEU", "india": "IND",
    "israel": "ISR", "ukraine": "UKR", "sudan": "SDN", "syria": "SYR",
    "yemen": "YEM", "nigeria": "NGA", "colombia": "COL", "mexico": "MEX",
    "indonesia": "IDN", "pakistan": "PAK", "turkey": "TUR", "egypt": "EGY",
    "south africa": "ZAF", "brazil": "BRA", "canada": "CAN", "australia": "AUS",
    "japan": "JPN", "kenya": "KEN", "ethiopia": "ETH", "somalia": "SOM",
    "afghanistan": "AFG", "iraq": "IRQ", "iran": "IRN", "lebanon": "LBN",
    "algeria": "DZA", "taiwan": "TWN", "myanmar": "MMR", "thailand": "THA"
}

# Explainable 9-Category Conflict Taxonomy Regex/Keywords
CONFLICT_TAXONOMY: Dict[str, List[str]] = {
    "armed_conflict": [
        "war", "battle", "clash", "troops", "fighting", "combat", "shelling",
        "airstrike", "bombardment", "artillery", "offensive", "assault"
    ],
    "violence_civilian": [
        "massacre", "civilian deaths", "atrocities", "execution", "casualties",
        "deadly attack", "civilians killed", "hostage"
    ],
    "military_escalation": [
        "missile test", "mobilization", "naval deployment", "military drill",
        "troop buildup", "air defense", "warplanes", "weapons shipment"
    ],
    "ceasefire_peace": [
        "ceasefire", "truce", "peace talks", "armistice", "peace negotiation",
        "peace agreement", "peace deal"
    ],
    "sanctions_economic": [
        "sanctions", "embargo", "trade restriction", "asset freeze",
        "economic penalties", "boycott"
    ],
    "displacement_refugees": [
        "refugees", "displaced", "asylum seekers", "fleeing",
        "humanitarian crisis", "refugee camp"
    ],
    "terrorism_insurgency": [
        "terrorist", "suicide bomber", "insurgency", "ambush", "guerrilla",
        "rebel group", "militants", "jihadist"
    ],
    "border_tensions": [
        "border clash", "border skirmish", "disputed border", "airspace violation",
        "border standoff", "territorial dispute"
    ],
    "diplomatic_escalation": [
        "ambassador recalled", "diplomatic expulsion", "severed ties",
        "ultimatum", "security treaty", "diplomatic crisis"
    ],
}

# Deterministic Lexical Sentiment Dictionary (Word -> Valence [-1.0, 1.0])
# Self-contained, zero-dependency, transparent NLP scoring
LEXICAL_SENTIMENT_DICT: Dict[str, float] = {
    # High-intensity negative conflict words
    "war": -0.8, "massacre": -1.0, "killed": -0.8, "deadly": -0.8, "fatal": -0.8,
    "death": -0.7, "crisis": -0.6, "threat": -0.6, "escalate": -0.6, "attack": -0.7,
    "bombing": -0.8, "missile": -0.5, "clash": -0.6, "fighting": -0.6, "terrorist": -0.9,
    "atrocity": -0.9, "collapse": -0.7, "danger": -0.6, "hostile": -0.6, "siege": -0.7,
    "sanctions": -0.5, "casualty": -0.7, "wound": -0.5, "refugee": -0.4, "displaced": -0.4,
    "flee": -0.5, "destroy": -0.7, "aggression": -0.7, "invasion": -0.8, "strike": -0.6,
    # High-intensity positive peace words
    "peace": 0.8, "ceasefire": 0.7, "truce": 0.7, "agreement": 0.6, "reconciliation": 0.7,
    "talks": 0.3, "treaty": 0.6, "diplomacy": 0.5, "stability": 0.6, "cooperation": 0.6,
    "aid": 0.4, "relief": 0.5, "recovery": 0.5, "dialogue": 0.4, "compromise": 0.5,
    "settlement": 0.5, "progress": 0.5, "resolve": 0.4, "protection": 0.5, "humanitarian": 0.3,
}
