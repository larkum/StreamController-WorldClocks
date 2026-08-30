from functools import lru_cache
from pathlib import Path
from zoneinfo import TZPATH, available_timezones


EXCLUDED_PREFIXES = ("posix/", "right/", "SystemV/")
EXCLUDED_NAMES = {"Factory", "localtime"}


# Cities that people commonly search for but that share another city's IANA
# timezone. The representative IANA city is added automatically.
MAJOR_CITY_ALIASES = {
    "Africa/Cairo": ("Alexandria", "Giza"),
    "Africa/Johannesburg": ("Cape Town", "Pretoria", "Durban"),
    "Africa/Lagos": ("Abuja", "Kano", "Ibadan"),
    "Africa/Nairobi": ("Mombasa",),
    "Africa/Casablanca": ("Rabat", "Marrakesh"),
    "Africa/Accra": ("Kumasi",),
    "America/New_York": (
        "Washington DC", "Boston", "Philadelphia", "Atlanta", "Miami",
        "Baltimore", "Charlotte", "Cleveland", "Pittsburgh",
    ),
    "America/Chicago": (
        "Dallas", "Houston", "Austin", "San Antonio", "Fort Worth",
        "Minneapolis", "St Louis", "New Orleans", "Oklahoma City",
    ),
    "America/Denver": ("Salt Lake City", "Albuquerque", "El Paso"),
    "America/Phoenix": ("Tucson",),
    "America/Los_Angeles": (
        "San Francisco", "San Diego", "Seattle", "Portland", "Las Vegas",
        "Sacramento", "San Jose",
    ),
    "America/Toronto": ("Ottawa", "Mississauga"),
    "America/Vancouver": ("Victoria",),
    "America/Edmonton": ("Calgary",),
    "America/Winnipeg": ("Regina", "Saskatoon"),
    "America/Mexico_City": ("Puebla", "Toluca"),
    "America/Monterrey": ("Saltillo",),
    "America/Sao_Paulo": (
        "Rio de Janeiro", "Brasilia", "Belo Horizonte", "Curitiba",
        "Porto Alegre",
    ),
    "America/Argentina/Buenos_Aires": ("La Plata",),
    "America/Bogota": ("Medellin", "Cali", "Cartagena"),
    "America/Lima": ("Arequipa",),
    "America/Santiago": ("Valparaiso",),
    "America/Caracas": ("Maracaibo",),
    "Asia/Kolkata": (
        "New Delhi", "Delhi", "Mumbai", "Bengaluru", "Bangalore",
        "Chennai", "Hyderabad", "Pune", "Ahmedabad", "Jaipur",
    ),
    "Asia/Shanghai": ("Beijing", "Guangzhou", "Shenzhen", "Chengdu", "Wuhan"),
    "Asia/Tokyo": ("Osaka", "Yokohama", "Kyoto", "Nagoya", "Sapporo"),
    "Asia/Seoul": ("Busan", "Incheon", "Daegu"),
    "Asia/Dubai": ("Abu Dhabi", "Sharjah"),
    "Asia/Riyadh": ("Jeddah", "Mecca", "Medina"),
    "Asia/Jakarta": ("Surabaya", "Bandung"),
    "Asia/Manila": ("Quezon City", "Cebu", "Davao"),
    "Asia/Karachi": ("Lahore", "Islamabad", "Rawalpindi"),
    "Asia/Dhaka": ("Chittagong", "Chattogram"),
    "Asia/Ho_Chi_Minh": ("Hanoi", "Da Nang"),
    "Asia/Bangkok": ("Chiang Mai", "Pattaya"),
    "Asia/Jerusalem": ("Tel Aviv", "Haifa"),
    "Asia/Tehran": ("Mashhad", "Isfahan", "Shiraz"),
    "Europe/London": (
        "Birmingham", "Manchester", "Glasgow", "Edinburgh", "Liverpool",
        "Cardiff", "Belfast",
    ),
    "Europe/Paris": ("Marseille", "Lyon", "Toulouse", "Nice"),
    "Europe/Berlin": ("Hamburg", "Munich", "Frankfurt", "Cologne"),
    "Europe/Madrid": ("Barcelona", "Valencia", "Seville"),
    "Europe/Rome": ("Milan", "Naples", "Turin", "Florence"),
    "Europe/Amsterdam": ("Rotterdam", "The Hague", "Utrecht"),
    "Europe/Brussels": ("Antwerp", "Ghent"),
    "Europe/Zurich": ("Geneva", "Basel", "Bern"),
    "Europe/Vienna": ("Graz", "Salzburg"),
    "Europe/Warsaw": ("Krakow", "Lodz", "Wroclaw"),
    "Europe/Moscow": ("Saint Petersburg", "St Petersburg", "Nizhny Novgorod"),
    "Europe/Istanbul": ("Ankara", "Izmir", "Bursa"),
    "Europe/Athens": ("Thessaloniki",),
    "Europe/Lisbon": ("Porto",),
    "Australia/Sydney": ("Canberra", "Newcastle"),
    "Australia/Melbourne": ("Geelong",),
    "Australia/Brisbane": ("Gold Coast", "Sunshine Coast"),
    "Australia/Perth": ("Fremantle",),
    "Pacific/Auckland": ("Wellington", "Christchurch"),
}


# Friendly state entries make searches such as "Texas" useful even though the
# underlying IANA zones are named after Chicago and Denver. Split states show
# each practical choice separately.
US_STATE_TIMEZONES = {
    "Alabama": (("America/Chicago", "Central Time"),),
    "Alaska": (("America/Anchorage", "Alaska Time (most areas)"), ("America/Adak", "Aleutian Islands")),
    "Arizona": (("America/Phoenix", "Mountain Time, no DST (most areas)"), ("America/Denver", "Mountain Time (Navajo Nation)")),
    "Arkansas": (("America/Chicago", "Central Time"),),
    "California": (("America/Los_Angeles", "Pacific Time"),),
    "Colorado": (("America/Denver", "Mountain Time"),),
    "Connecticut": (("America/New_York", "Eastern Time"),),
    "Delaware": (("America/New_York", "Eastern Time"),),
    "District of Columbia": (("America/New_York", "Eastern Time"),),
    "Florida": (("America/New_York", "Eastern Time (most areas)"), ("America/Chicago", "Central Time (western panhandle)")),
    "Georgia": (("America/New_York", "Eastern Time"),),
    "Hawaii": (("Pacific/Honolulu", "Hawaii Time"),),
    "Idaho": (("America/Boise", "Mountain Time (south)"), ("America/Los_Angeles", "Pacific Time (north)")),
    "Illinois": (("America/Chicago", "Central Time"),),
    "Indiana": (("America/Indiana/Indianapolis", "Eastern Time (most areas)"), ("America/Chicago", "Central Time (some northwest and southwest counties)")),
    "Iowa": (("America/Chicago", "Central Time"),),
    "Kansas": (("America/Chicago", "Central Time (most areas)"), ("America/Denver", "Mountain Time (far west)")),
    "Kentucky": (("America/Kentucky/Louisville", "Eastern Time (east)"), ("America/Chicago", "Central Time (west)")),
    "Louisiana": (("America/Chicago", "Central Time"),),
    "Maine": (("America/New_York", "Eastern Time"),),
    "Maryland": (("America/New_York", "Eastern Time"),),
    "Massachusetts": (("America/New_York", "Eastern Time"),),
    "Michigan": (("America/Detroit", "Eastern Time (most areas)"), ("America/Chicago", "Central Time (western Upper Peninsula)")),
    "Minnesota": (("America/Chicago", "Central Time"),),
    "Mississippi": (("America/Chicago", "Central Time"),),
    "Missouri": (("America/Chicago", "Central Time"),),
    "Montana": (("America/Denver", "Mountain Time"),),
    "Nebraska": (("America/Chicago", "Central Time (east)"), ("America/Denver", "Mountain Time (west)")),
    "Nevada": (("America/Los_Angeles", "Pacific Time (most areas)"), ("America/Denver", "Mountain Time (small border communities)")),
    "New Hampshire": (("America/New_York", "Eastern Time"),),
    "New Jersey": (("America/New_York", "Eastern Time"),),
    "New Mexico": (("America/Denver", "Mountain Time"),),
    "New York": (("America/New_York", "Eastern Time"),),
    "North Carolina": (("America/New_York", "Eastern Time"),),
    "North Dakota": (("America/Chicago", "Central Time (most areas)"), ("America/Denver", "Mountain Time (southwest)")),
    "Ohio": (("America/New_York", "Eastern Time"),),
    "Oklahoma": (("America/Chicago", "Central Time"),),
    "Oregon": (("America/Los_Angeles", "Pacific Time (most areas)"), ("America/Boise", "Mountain Time (most of Malheur County)")),
    "Pennsylvania": (("America/New_York", "Eastern Time"),),
    "Rhode Island": (("America/New_York", "Eastern Time"),),
    "South Carolina": (("America/New_York", "Eastern Time"),),
    "South Dakota": (("America/Chicago", "Central Time (east)"), ("America/Denver", "Mountain Time (west)")),
    "Tennessee": (("America/New_York", "Eastern Time (east)"), ("America/Chicago", "Central Time (middle and west)")),
    "Texas": (("America/Chicago", "Central Time (most areas)"), ("America/Denver", "Mountain Time (El Paso and Hudspeth County)")),
    "Utah": (("America/Denver", "Mountain Time"),),
    "Vermont": (("America/New_York", "Eastern Time"),),
    "Virginia": (("America/New_York", "Eastern Time"),),
    "Washington": (("America/Los_Angeles", "Pacific Time"),),
    "West Virginia": (("America/New_York", "Eastern Time"),),
    "Wisconsin": (("America/Chicago", "Central Time"),),
    "Wyoming": (("America/Denver", "Mountain Time"),),
}


COUNTRY_DISPLAY_OVERRIDES = {
    "GB": "United Kingdom (UK)",
    "US": "United States (USA)",
    "KR": "South Korea",
    "KP": "North Korea",
    "RU": "Russia",
    "TW": "Taiwan",
    "CZ": "Czech Republic (Czechia)",
    "TR": "Turkey (Türkiye)",
    "AE": "United Arab Emirates (UAE)",
    "GS": "South Georgia & South Sandwich Is.",
}


def _read_tab_file(filename: str):
    for root in TZPATH:
        path = Path(root) / filename
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
    return []


@lru_cache(maxsize=1)
def _country_names() -> dict[str, str]:
    names = {}
    for line in _read_tab_file("iso3166.tab"):
        if not line or line.startswith("#"):
            continue
        code, name = line.split("\t", 1)
        names[code] = COUNTRY_DISPLAY_OVERRIDES.get(code, name)
    return names


@lru_cache(maxsize=1)
def _zone_metadata() -> dict[str, tuple[tuple[str, ...], str]]:
    metadata = {}
    lines = _read_tab_file("zone1970.tab") or _read_tab_file("zone.tab")
    for line in lines:
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) < 3:
            continue
        country_codes, _, zone, *comment = columns
        metadata[zone] = (tuple(country_codes.split(",")), comment[0] if comment else "")
    return metadata


def _state_choices() -> list[tuple[str, str]]:
    choices = []
    for state, zones in US_STATE_TIMEZONES.items():
        for zone, detail in zones:
            compact_detail = detail.replace(" Time", "")
            compact_detail = compact_detail.replace("most areas", "most")
            compact_detail = compact_detail.replace(
                "El Paso and Hudspeth County", "El Paso area"
            )
            compact_detail = compact_detail.replace(
                "some northwest and southwest counties", "NW/SW"
            )
            compact_detail = compact_detail.replace(
                "small border communities", "border areas"
            )
            compact_detail = compact_detail.replace(
                "western Upper Peninsula", "western UP"
            )
            compact_detail = compact_detail.replace(
                "most of Malheur County", "Malheur Co."
            )
            compact_detail = compact_detail.replace(
                "middle and west", "central/west"
            )
            choices.append((zone, f"{state}: {compact_detail} · {zone}"))
    return choices


def _place_and_country(zone: str, country_names, metadata) -> tuple[str, str]:
    city = zone.rsplit("/", 1)[-1].replace("_", " ")
    country_codes, _ = metadata.get(zone, ((), ""))
    country = country_names.get(country_codes[0], country_codes[0]) if country_codes else ""
    return city, country


def _short_label(place: str, country: str, zone: str) -> str:
    if country and place.casefold() in country.casefold():
        location = country
    else:
        location = f"{place} — {country}" if country else place
    return f"{location} · {zone}"


def _alias_choices(country_names, metadata) -> list[tuple[str, str]]:
    choices = []
    for zone, aliases in MAJOR_CITY_ALIASES.items():
        for alias in aliases:
            choices.append((zone, _short_label(alias, "", zone)))
    return choices


def _country_choices(country_names, metadata) -> list[tuple[str, str]]:
    choices = []
    for zone, (country_codes, _) in metadata.items():
        city = zone.rsplit("/", 1)[-1].replace("_", " ")
        for code in country_codes:
            country = country_names.get(code, code)
            choices.append((zone, _short_label(city, country, zone)))
    return choices


@lru_cache(maxsize=1)
def timezone_choices() -> tuple[tuple[str, str], ...]:
    """Return searchable (IANA value, geographic display label) choices."""
    country_names = _country_names()
    metadata = _zone_metadata()

    choices = [("UTC", "UTC · Coordinated Universal Time")]

    for zone in sorted(available_timezones()):
        if zone in EXCLUDED_NAMES or zone.startswith(EXCLUDED_PREFIXES):
            continue
        city, _ = _place_and_country(zone, country_names, metadata)
        choices.append((zone, _short_label(city, "", zone)))

    # Aliases and state-specific rows are separate entries. This keeps every
    # visible row short while preserving all of the geographic search terms.
    choices.extend(_alias_choices(country_names, metadata))
    choices.extend(_country_choices(country_names, metadata))
    choices.extend(_state_choices())

    return tuple(choices)
