# -*- coding: utf-8 -*-
"""Standardize crawler undercarriage part names."""

RAW_TO_STANDARD = {
    "track roller": "Track Roller",
    "bottom roller": "Track Roller",
    "lower roller": "Track Roller",
    "roller": "Track Roller",
    "支重轮": "Track Roller",
    "单边支重轮": "Track Roller",
    "双边支重轮": "Track Roller",
    "carrier roller": "Carrier Roller",
    "top roller": "Carrier Roller",
    "upper roller": "Carrier Roller",
    "托链轮": "Carrier Roller",
    "托轮": "Carrier Roller",
    "idler": "Idler",
    "front idler": "Idler",
    "idler wheel": "Idler",
    "引导轮": "Idler",
    "导向轮": "Idler",
    "sprocket": "Sprocket",
    "drive sprocket": "Sprocket",
    "sprocket rim": "Sprocket",
    "sprocket segment": "Sprocket",
    "驱动齿": "Sprocket",
    "驱动轮": "Sprocket",
    "track link": "Track Chain",
    "track chain": "Track Chain",
    "link assembly": "Track Chain",
    "chain": "Track Chain",
    "链条": "Track Chain",
    "履带链": "Track Chain",
    "track shoe": "Track Shoe",
    "grouser shoe": "Track Shoe",
    "履带板": "Track Shoe",
    "track group": "Track Group",
    "track assembly": "Track Group",
    "履带总成": "Track Group",
    "track adjuster": "Track Adjuster",
    "adjuster assembly": "Track Adjuster",
    "track tensioner": "Track Adjuster",
    "tensioner": "Track Adjuster",
    "涨紧总成": "Track Adjuster",
    "涨紧装置": "Track Adjuster",
}

STANDARD_TO_CN = {
    "Track Roller": "支重轮",
    "Carrier Roller": "托链轮",
    "Idler": "引导轮",
    "Sprocket": "驱动齿",
    "Track Chain": "链条",
    "Track Shoe": "履带板",
    "Track Group": "履带总成",
    "Track Adjuster": "涨紧总成",
}

NON_CRAWLER_KEYWORDS = [
    "engine",
    "filter",
    "oil",
    "hydraulic",
    "pump",
    "motor",
    "seal",
    "bearing",
    "gasket",
    "hose",
    "pipe",
    "valve",
    "cylinder",
    "radiator",
    "turbo",
    "alternator",
    "starter",
    "battery",
    "sensor",
    "switch",
    "lamp",
    "light",
    "mirror",
    "winch",
    "counterweight",
    "cab",
    "seat",
    "glass",
]

UNDERCARRIAGE_KEYWORDS = [
    "track",
    "roller",
    "sprocket",
    "idler",
    "shoe",
    "chain",
    "link",
    "履带",
    "支重轮",
    "托链轮",
    "引导轮",
    "驱动齿",
    "驱动轮",
    "链条",
    "链轨",
    "履带板",
    "涨紧",
]


def standardize_name(original_name):
    """Return original name, standard English name, and standard Chinese name."""
    name_lower = (original_name or "").lower().strip()
    standard_en = RAW_TO_STANDARD.get(name_lower, "")
    if not standard_en:
        for raw, std in RAW_TO_STANDARD.items():
            raw_lower = raw.lower()
            if raw_lower in name_lower or name_lower in raw_lower:
                standard_en = std
                break
    cn = STANDARD_TO_CN.get(standard_en, "待分类")
    return original_name, standard_en, cn


def is_crawler_part(name, description=""):
    """Return True when the text looks like a crawler undercarriage part."""
    text = f"{name or ''} {description or ''}".lower()
    if any(keyword in text for keyword in NON_CRAWLER_KEYWORDS):
        return False
    return any(keyword in text for keyword in UNDERCARRIAGE_KEYWORDS)
