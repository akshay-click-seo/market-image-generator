"""
units.py
Full unit-of-measure list used across market/commodity reports (matches the
dropdown options commonly seen on report sites: Kilogramos, Millones,
Toneladas, Barriles, MW, GWh, etc.), plus regex-detection helpers so the
Auto Fetch parser can recognize any of these units in pasted report text,
not just "Million/Billion".

Units are stored as (display_label, short_code) pairs. `short_code` is what
gets used inside generated images (kept short so it fits on stat cards);
`display_label` is what shows in the Streamlit dropdown.
"""

import re


# (display label shown in the UI dropdown, short label used in generated images)
UNIT_OPTIONS = [
    ("Millones", "Millones"),
    ("Mil Millones", "Mil Millones"),
    ("Billones", "Billones"),
    ("Kilogramos", "Kg"),
    ("Millones de B/d", "MM B/d"),
    ("Millones de Bushels", "MM Bushels"),
    ("Mil Millones de Barriles", "MM Millones Barriles"),
    ("Millones de Dosis", "MM Dosis"),
    ("Toneladas CWE", "Ton CWE"),
    ("B/D", "B/D"),
    ("GWh", "GWh"),
    ("Pies Lineales", "Pies Lineales"),
    ("Millones de Cajas de 9 Litros", "MM Cajas 9L"),
    ("por Unidad por Mes", "por Unidad/Mes"),
    ("Miles de Toneladas", "Mil Ton"),
    ("Mil Millones de Toneladas-Milla", "MM Ton-Milla"),
    ("GW Térmico", "GW Térmico"),
    ("Miles de Barriles", "Mil Barriles"),
    ("MMCF", "MMCF"),
    ("MW", "MW"),
    ("Millones de HL", "MM HL"),
    ("GJ", "GJ"),
    ("Kilolitro", "Kilolitro"),
    ("Millones de Cajas", "MM Cajas"),
    ("kMT-LCE", "kMT-LCE"),
    ("Miles de CBM", "Mil CBM"),
    ("KB/d", "KB/d"),
    ("MB/d", "MB/d"),
    ("TMT", "TMT"),
    ("Gigavatios", "GW"),
    ("KMT", "KMT"),
    ("MMT", "MMT"),
    ("Millones de Docenas", "MM Docenas"),
    ("1000 Unidades", "1000 Unidades"),
    ("MWh", "MWh"),
    ("TWh", "TWh"),
    ("Megavatios", "MW"),
    ("Teravatios", "TW"),
    ("Miles de Unidades", "Mil Unidades"),
    ("Billones de USD", "Bn USD"),
    ("Mil Millones de USD", "Mil MM USD"),
    ("Millones de USD", "MM USD"),
    ("Miles de USD", "Mil USD"),
    ("Miles", "Miles"),
    ("Unidad", "Unidad"),
    ("PJ", "PJ"),
    ("Millones de Litros", "MM Litros"),
    ("Mil Millones de Litros", "Mil MM Litros"),
    ("Billones de Litros", "Bn Litros"),
    ("Millones de Unidades", "MM Unidades"),
    ("Mil Millones de Unidades", "Mil MM Unidades"),
    ("Billones de Unidades", "Bn Unidades"),
    ("Millones de Toneladas", "MM Toneladas"),
    ("Mil Millones de Toneladas", "Mil MM Toneladas"),
    ("Billones de Toneladas", "Bn Toneladas"),
    ("Toneladas Métricas", "Ton Métricas"),
    ("Kilotoneladas", "Kilotoneladas"),
    ("Toneladas LCE", "Ton LCE"),
    ("Millones de Toneladas LCE", "MM Ton LCE"),
    ("Mil Millones de Toneladas LCE", "Mil MM Ton LCE"),
    ("Billones de Toneladas LCE", "Bn Ton LCE"),
    ("Millones de Metros Cubicos", "MM m³"),
    ("Mil Millones de Metros Cubicos", "Mil MM m³"),
    ("Billones de Metros Cuubicos", "Bn m³"),
    ("Millones de Metros Cuadrados", "MM m²"),
    ("Mil Millones de Metros Cuadrados", "Mil MM m²"),
    ("Billones de Metros Cuadrados", "Bn m²"),
    ("Kilotoneladas LCE", "Kt LCE"),
    ("Toneladas", "Toneladas"),
    ("Crore", "Crore"),
    ("Crores", "Crores"),
    ("Billones", "Billones"),
    ("Mil Millones", "Mil Millones"),
    ("Millones de barriles", "MM Barriles"),
    ("Mil toneladas métricas", "Mil Ton Métricas"),
    ("Unidades", "Unidades"),
    # Kept for backward compatibility with existing generated-image logic
    ("Million", "Millones"),
    ("Billion", "Mil Millones"),
]

# Deduplicated display labels, in original order, for populating dropdowns.
UNIT_LABELS = list(dict.fromkeys(label for label, _ in UNIT_OPTIONS))

_LABEL_TO_SHORT = dict(UNIT_OPTIONS)


def short_label(unit_label):
    """Return the compact label used inside generated images for a given
    unit dropdown selection (falls back to the label itself if unknown)."""
    return _LABEL_TO_SHORT.get(unit_label, unit_label)


# Longest-label-first so e.g. "Mil Millones de Toneladas LCE" matches before
# the shorter "Toneladas" when scanning pasted report text.
_UNIT_PATTERNS = sorted(
    {label for label in UNIT_LABELS if label not in ("Million", "Billion")},
    key=len, reverse=True,
)

UNIT_DETECT_REGEX = re.compile(
    "(" + "|".join(re.escape(u) for u in _UNIT_PATTERNS) + r"|Million|Billion)",
    re.IGNORECASE,
)


def detect_unit(text):
    """Scan free text for any known unit label (case-insensitive) and return
    the canonical display label, or None if nothing matched."""
    if not text:
        return None
    match = UNIT_DETECT_REGEX.search(text)
    if not match:
        return None
    found = match.group(1)
    # Normalize the classic English "Million"/"Billion" to their Spanish
    # canonical labels first (checked before the generic loop below, since
    # "Million"/"Billion" also appear verbatim in UNIT_LABELS for backward
    # compatibility with old generated-image calls).
    if found.lower() == "million":
        return "Millones"
    if found.lower() == "billion":
        return "Mil Millones"
    # Normalize casing back to the canonical stored label
    for label in UNIT_LABELS:
        if label.lower() == found.lower():
            return label
    return found
