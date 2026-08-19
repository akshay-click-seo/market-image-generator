"""
parser.py
Regex-based auto-extraction of market report figures from a pasted paragraph.

Handles common IMARC / Informes de Expertos (IDE) style report sentences, e.g.:

  "The market reached USD 145 Million in 2025 and is expected to reach
   USD 367.3 Million by 2035, growing at a CAGR of 9.74% during 2026-2035."

  "El mercado alcanzo un valor de USD 2.4 Mil Millones en 2025 y se espera
   que alcance USD 29.8 Mil Millones para 2036, creciendo a una CAGR del
   25.8% durante el periodo de pronostico 2025-2036."

No LLM / network calls -- pure regex + light heuristics, so it runs fully
offline.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional

from utils.units import detect_unit as _detect_unit_from_list, UNIT_DETECT_REGEX
from utils.numfmt import parse_es_number as _parse_es_number


CURRENCY_SYMBOLS = {
    "$": "USD", "USD": "USD", "US$": "USD",
    "€": "EUR", "EUR": "EUR",
    "£": "GBP", "GBP": "GBP",
    "₹": "INR", "INR": "INR", "RS": "INR", "RS.": "INR",
    "¥": "JPY", "JPY": "JPY", "CNY": "CNY", "RMB": "CNY",
}

# "Mil Millones" (ES, = Billion) / "Millones" (ES, = Million) / "Billion" / "Million" / "Bn" / "Mn"
UNIT_MULTIPLIERS = {
    "mil millones": 1_000,   # expressed relative to "Millones" base unit -> normalized to Millions
    "billion": 1_000,
    "bn": 1_000,
    "million": 1,
    "millones": 1,
    "mn": 1,
    "m": 1,
    "trillion": 1_000_000,
}

# Captures a full numeric token, in EITHER English (1,234.56) or Spanish
# (1.234,56) convention -- deliberately does NOT assume which of "." / ","
# is the thousands separator vs. the decimal separator at the regex level
# (that ambiguity is resolved afterwards by _clean_number()/parse_es_number(),
# which looks at which separator appears LAST). The old pattern
# (`\d[\d,]*(?:\.\d+)?`) only allowed a SINGLE trailing dot-group and
# treated every comma as a free-floating thousands separator -- so a
# Spanish-formatted paste like "9.173,23" matched only as far as "9.173"
# (the ",23" decimal tail was left over, silently dropped), corrupting
# 9173.23 down to 9.173. Matching the whole digit/dot/comma run instead
# (anchored to start AND end on a digit, so trailing sentence punctuation
# like "9.173,23." never gets swept in) preserves every digit the user
# pasted.
NUM = r"(?:USD|US\$|\$|€|£|₹|¥)?\s*(\d(?:[\d.,]*\d)?)"


@dataclass
class ExtractedData:
    start_value: Optional[float] = None
    end_value: Optional[float] = None
    base_year: Optional[int] = None
    forecast_year: Optional[int] = None
    forecast_period: Optional[str] = None
    cagr: Optional[float] = None
    currency: Optional[str] = None
    unit: Optional[str] = None  # "Million" or "Billion" (normalized display unit)
    market_name: Optional[str] = None
    region: Optional[str] = None
    raw_text: str = ""

    def to_dict(self):
        return asdict(self)


_MISSING = object()


def _clean_number(s):
    """Parse a matched numeric string to float, correctly handling BOTH
    English (1,234.56) and Spanish (1.234,56 / 0,18) decimal conventions --
    delegates to the same locale-aware parser used by the manual number
    input fields, so pasted report text and manually-typed values are
    interpreted identically. A naive '.replace(",", "")' (the old
    implementation) corrupted Spanish decimals like "0,18" into "018" (=18)
    by treating the decimal comma as an English thousands separator.
    Returns None (never raises) if the match is malformed."""
    cleaned = s.strip()
    if not cleaned:
        return None
    result = _parse_es_number(cleaned, default=_MISSING)
    return None if result is _MISSING else result


def _detect_currency(text):
    upper = text.upper()
    for sym, code in CURRENCY_SYMBOLS.items():
        if sym in upper or sym in text:
            return code
    return "USD"


def _detect_unit(text):
    """Detect the unit of measure mentioned in free text. Recognizes the full
    report unit list (Millones, Toneladas, Barriles, MW, GWh, ...) in
    addition to the classic Million/Billion, defaulting to 'Millones' if
    nothing is found."""
    found = _detect_unit_from_list(text)
    if found:
        return found
    lower = text.lower()
    if re.search(r"\bbn\b", lower):
        return "Mil Millones"
    if re.search(r"\bmn\b", lower):
        return "Millones"
    return "Millones"


def extract_from_text(text: str) -> ExtractedData:
    """Best-effort regex extraction of market figures from a free-text paragraph."""
    result = ExtractedData(raw_text=text)
    if not text or not text.strip():
        return result

    t = text.strip()
    currency = _detect_currency(t)
    unit = _detect_unit(t)
    result.currency = currency
    result.unit = unit

    # --- Market name + region/country, from a title line like "Mercado
    # Latinoamericano de Maltodextrina" or "Mercado de Maltodextrina en México"
    market_name, region = _extract_title_info(t)
    result.market_name = market_name
    result.region = region

    # --- CAGR: "CAGR of 9.74%" / "CAGR del 25.8%" / "growing at a CAGR of X%" /
    # "Tasa de Crecimiento Anual Compuesta (CAGR) de 2026 a 2035: 4,70 %" (the
    # last form has the forecast-period years sitting BETWEEN "CAGR" and the
    # value -- tried first since it's more specific; the plain "CAGR ... X%"
    # patterns below require NO digits in that gap, so they never match the
    # embedded-years form and are tried only as a fallback).
    cagr_match = re.search(
        r"CAGR\)?\s*(?:de|from|durante|during)?\s*20\d{2}\s*(?:[-–—aA]|to)\s*20\d{2}\s*[:\-]?\s*([\d]+(?:[.,]\d+)?)\s*%",
        t, re.IGNORECASE,
    )
    if not cagr_match:
        cagr_match = re.search(
            r"CAGR[^%\d]{0,15}?([\d]+(?:[.,]\d+)?)\s*%", t, re.IGNORECASE
        )
    if not cagr_match:
        cagr_match = re.search(r"([\d]+(?:[.,]\d+)?)\s*%\s*CAGR", t, re.IGNORECASE)
    if cagr_match:
        result.cagr = _clean_number(cagr_match.group(1))

    # --- Forecast period: "during 2026-2035" / "2025-2036" / "durante el periodo ... 2026 - 2035"
    period_match = re.search(r"(20\d{2})\s*[-–—aA]{1,3}\s*(20\d{2})", t)
    if period_match:
        y1, y2 = int(period_match.group(1)), int(period_match.group(2))
        result.forecast_period = f"{y1}-{y2}"

    _unit_group = UNIT_DETECT_REGEX.pattern.strip("()")

    # --- Base year value.
    # Preferred: structured "Tamaño del Mercado en 2025: 0,18 MMT" / "Market
    # Size in 2025: 0.18 MMT" layout -- the YEAR comes BEFORE the value,
    # common in bulleted report summaries ("* Tamaño del Mercado en 2025: ...").
    # Falls back to the older flowing-sentence layout ("... reached USD 145
    # Million in 2025", value BEFORE the year) if the structured form isn't found.
    base_match = re.search(
        r"(?:Tama[ñn]o del Mercado|Market Size)\s*(?:en|in)\s+(20\d{2})\s*[:\-]?\s*"
        + NUM + r"\s*(" + _unit_group + r"|bn|mn)?",
        t, re.IGNORECASE,
    )
    if base_match:
        result.start_value = _clean_number(base_match.group(2))
        result.base_year = int(base_match.group(1))
        if base_match.group(3):
            result.unit = _detect_unit(base_match.group(3))
    else:
        base_match = re.search(
            NUM + r"\s*(" + _unit_group + r"|bn|mn)?\s*(?:.{0,20}?)\b(?:in|en)\s+(20\d{2})",
            t, re.IGNORECASE
        )
        if base_match:
            result.start_value = _clean_number(base_match.group(1))
            result.base_year = int(base_match.group(3))
            if base_match.group(2):
                result.unit = _detect_unit(base_match.group(2))

    # --- End/forecast value.
    # Preferred: structured "Tamaño del Mercado Proyectado en 2035: 0,28 MMT"
    # layout (year before value; requires a qualifier word like
    # "Proyectado"/"Projected"/"Estimado" so it targets the SECOND bullet,
    # not re-matching the same generic "Tamaño del Mercado" phrase the base
    # value pattern above already consumed). Falls back to the older
    # flowing-sentence layout ("... reach USD 367.3 Million by 2035").
    end_match = re.search(
        r"(?:Tama[ñn]o del Mercado (?:Proyectado|Estimado|Pronosticado)|Projected Market Size|"
        r"Forecast(?:ed)? Market Size|Estimated Market Size)\s*(?:en|in|para|by)\s+(20\d{2})\s*[:\-]?\s*"
        + NUM + r"\s*(" + _unit_group + r"|bn|mn)?",
        t, re.IGNORECASE,
    )
    if end_match:
        result.end_value = _clean_number(end_match.group(2))
        result.forecast_year = int(end_match.group(1))
        if end_match.group(3):
            result.unit = _detect_unit(end_match.group(3))
    else:
        end_match = re.search(
            NUM + r"\s*(" + _unit_group + r"|bn|mn)?\s*(?:.{0,20}?)\b(?:by|para|para el año|hacia)\s+(20\d{2})",
            t, re.IGNORECASE
        )
        if end_match:
            result.end_value = _clean_number(end_match.group(1))
            result.forecast_year = int(end_match.group(3))
            if end_match.group(2):
                result.unit = _detect_unit(end_match.group(2))

    # --- Fallbacks: if base/end not matched via "in/by" pattern, fall back to first two
    # currency-prefixed numbers found in order of appearance.
    if result.start_value is None or result.end_value is None:
        all_nums = re.findall(NUM, t)
        if all_nums:
            nums = [n for n in (_clean_number(x) for x in all_nums) if n is not None]
            if result.start_value is None and len(nums) >= 1:
                result.start_value = nums[0]
            if result.end_value is None and len(nums) >= 2:
                result.end_value = nums[-1]

    # --- Fallback years from forecast_period if base/forecast year missing
    if result.forecast_period:
        y1, y2 = result.forecast_period.split("-")
        if result.base_year is None:
            result.base_year = int(y1) - 1  # base year is typically one before forecast start
        if result.forecast_year is None:
            result.forecast_year = int(y2)

    # --- Last-resort: any 4 distinct years mentioned, use min/max
    if result.base_year is None or result.forecast_year is None:
        years = sorted(set(int(y) for y in re.findall(r"\b(20\d{2})\b", t)))
        if years:
            if result.base_year is None:
                result.base_year = years[0]
            if result.forecast_year is None:
                result.forecast_year = years[-1]

    return result


def compute_cagr(start_value, end_value, num_years):
    """Compute CAGR (%) given start value, end value, and number of years."""
    if start_value is None or end_value is None or num_years is None or num_years <= 0:
        return None
    if start_value <= 0:
        return None
    return (((end_value / start_value) ** (1 / num_years)) - 1) * 100


def generate_yearly_values(start_value, cagr_pct, num_years):
    """Auto-calculate yearly bar values by compounding start_value at cagr_pct
    across num_years steps (inclusive of start year as year 0)."""
    if start_value is None or cagr_pct is None or num_years is None:
        return []
    rate = cagr_pct / 100.0
    return [round(start_value * ((1 + rate) ** i), 2) for i in range(num_years + 1)]


# --- Market name / region extraction -----------------------------------------

# Demonym/adjective AND plain region-noun forms (Spanish + English) ->
# canonical region display name, for titles like "Mercado Latinoamericano
# de X" (adjective) or "Latin America X Market" / "Latin American X Market"
# (noun/adjective, both common in English report titles). Each entry lists
# its more specific/longer alternatives first so e.g. "asia pacific"
# matches before the bare "asia" fallback would.
_REGION_ADJECTIVES = [
    (r"latinoamericano|latinoamericana|latin\s+american|latin\s+america", "Latinoamérica"),
    (r"norteamericano|norteamericana|north\s+american|north\s+america", "Norteamérica"),
    (r"asia[\s-]pac[ií]fico|asia[\s-]pacific", "Asia-Pacífico"),
    (r"asi[aá]tico|asi[aá]tica|asian|asia", "Asia-Pacífico"),
    (r"europeo|europea|european|europe", "Europa"),
    (r"africano|africana|african|africa", "África"),
    (r"medio\s+oriente|middle\s+eastern|middle\s+east", "Medio Oriente"),
    (r"mundial|global|worldwide", "Global"),
]

_NAME_CHARS = r"[\w\sÀ-ÿ\-]"

# Common trailing report-title words ("Maltodextrin Market Size, Share and
# Growth Report" / "Mercado ... Tamaño y Pronóstico") that a non-greedy
# capture can otherwise swallow when there's no colon/newline to stop at.
# Trimming the capture at the first of these keeps just the actual
# name/region instead of a whole trailing clause.
_TITLE_STOPWORDS_RE = re.compile(
    r"\b(?:Size|Share|Growth|Report|Reports|Forecast|Forecasts|Analysis|Trend|Trends|Outlook|"
    r"Industry|Overview|Statistics|Insights|Research|Study|Segmentation|Regional|Global|"
    r"Tama[ñn]o|An[aá]lisis|Informe|Pron[oó]stico|Estudio|Segmentaci[oó]n|Tendencias)\b",
    re.IGNORECASE,
)


def _trim_at_stopword(s):
    """Cut a captured name/region string at the first trailing report-title
    stopword (see _TITLE_STOPWORDS_RE), so a non-greedy regex capture that
    had nowhere else to stop doesn't swallow a whole trailing clause like
    'Size, Share and Growth Report'."""
    m = _TITLE_STOPWORDS_RE.search(s)
    if m:
        s = s[:m.start()]
    return s.strip(" ,.-")


def _extract_title_info(text):
    """Best-effort extraction of (market_name, region) from a report title
    line, e.g. 'Mercado Latinoamericano de Maltodextrina' -> market name
    'Maltodextrina', region 'Latinoamérica'. Either or both may come back
    None -- this is opportunistic prefill for an editable field, not a
    strict parse, so a miss is harmless."""
    if not text:
        return None, None

    # Spanish: "Mercado {Adjective} de {Name}" -- region implied by the
    # adjective itself (no explicit country/region name in the text).
    for pattern, region in _REGION_ADJECTIVES:
        m = re.search(
            r"Mercado\s+(?:" + pattern + r")\s+de\s+(" + _NAME_CHARS + r"{1,60}?)(?:\s*[:：\n]|$)",
            text, re.IGNORECASE,
        )
        if m:
            name = _trim_at_stopword(m.group(1))
            if name:
                return _title_case_label(name), region

    # Spanish: "Mercado de {Name} en {Country}"
    m = re.search(
        r"Mercado\s+de\s+(" + _NAME_CHARS + r"{1,60}?)\s+en\s+([A-Za-zÀ-ÿ][\w\sÀ-ÿ\-]{1,40}?)(?:\s*[:：\n]|$)",
        text, re.IGNORECASE,
    )
    if m:
        name = _trim_at_stopword(m.group(1))
        country = _trim_at_stopword(m.group(2))
        if name and country:
            return _title_case_label(name), _title_case_label(country)

    # Spanish: generic "Mercado de {Name}" (no region/country mentioned)
    m = re.search(r"Mercado\s+de\s+(" + _NAME_CHARS + r"{1,60}?)(?:\s*[:：\n]|$)", text, re.IGNORECASE)
    if m:
        name = _trim_at_stopword(m.group(1))
        if name:
            return _title_case_label(name), None

    # English patterns below deliberately do NOT use re.IGNORECASE on the
    # literal word "Market" (only the region-adjective alternation is
    # case-folded via the inline (?i:...) group). A capitalized "Market" is
    # a strong signal of an actual title/proper-noun phrase; matching
    # lowercase "market" too would false-positive on ordinary descriptive
    # sentences like "The market reached USD 145 Million in 2025..." --
    # capturing garbage like "The" as the market name.

    # English: "{Region} {Name} Market" -- region implied by a leading demonym
    for pattern, region in _REGION_ADJECTIVES:
        m = re.search(r"\b(?i:" + pattern + r")\s+(" + _NAME_CHARS + r"{1,60}?)\s+Market\b", text)
        if m:
            name = _trim_at_stopword(m.group(1))
            if name:
                return _title_case_label(name), region

    # English: "{Name} Market in {Country}"
    m = re.search(
        r"([A-Za-z0-9][\w\s\-]{1,60}?)\s+Market\s+in\s+([A-Za-z][\w\s\-]{1,40}?)(?:\s*[:：\n]|$)",
        text,
    )
    if m:
        name = _trim_at_stopword(m.group(1))
        country = _trim_at_stopword(m.group(2))
        if name and country:
            return _title_case_label(name), _title_case_label(country)

    # English: generic "{Name} Market" (no region/country mentioned)
    m = re.search(r"([A-Za-z0-9][\w\s\-]{1,60}?)\s+Market\b", text)
    if m:
        name = _trim_at_stopword(m.group(1))
        if name:
            return _title_case_label(name), None

    return None, None


# --- Segmentation extraction -------------------------------------------------

# Category headers commonly used to introduce a segmentation dimension in
# IMARC / Informes de Expertos style reports, e.g. "By Product Type:" or
# "Por Tipo de Producto:".
_SEGMENT_CATEGORY_WORDS = [
    "product type", "tipo de producto", "application", "aplicación", "aplicacion",
    "source", "fuente", "distribution channel", "canal de distribución", "canal de distribucion",
    "region", "región", "región", "end user", "usuario final", "type", "tipo",
    "component", "componente", "technology", "tecnología", "tecnologia",
    "industry vertical", "vertical de la industria", "deployment mode", "modo de implementación",
]

_LABELED_SEGMENT_RE = re.compile(
    r"\b(?:by|por)\s+([A-Za-zÀ-ÿ][\w\sÀ-ÿ]{2,40}?)\s*[:：]",
    re.IGNORECASE,
)

# "segmented by X, Y, and Z" / "segmentado por X, Y y Z" / "segmentarse en
# base a X, Y y Z" — captures the list tail after a segmentation verb
# phrase, up to a sentence boundary.
_SEGMENT_LIST_INTRO_RE = re.compile(
    r"(?:segment(?:ed|ación|acion)?\s*(?:can\s+be\s+)?(?:based\s+on|by)"
    r"|segmentars?e\s+(?:en\s+base\s+a|por)"
    r"|segmentad[oa]\s+(?:en\s+base\s+a|por))\s+"
    r"([^.]{3,250})",
    re.IGNORECASE,
)

# "... por los Siguientes Segmentos:" / "... by the Following Segments:" --
# an "Alcance del Informe" (report scope) style introducer where each
# segment name is listed on its OWN LINE below the colon, rather than as a
# comma-separated list on the same line, e.g.:
#   "...Análisis Histórico y Previsiones del Mercado por los Siguientes
#   Segmentos:
#   Aplicación
#   País"
_SEGMENT_LINES_INTRO_RE = re.compile(
    r"(?:siguientes\s+segmentos|following\s+segments)\s*[:：]\s*",
    re.IGNORECASE,
)


def _split_list_tail(tail):
    """Split a trailing 'A, B, C and D' / 'A, B y C' clause into clean items,
    stripping any repeated 'by'/'por' prefix that leaks in from patterns
    like 'by X, by Y, and by Z'."""
    # Normalize "and"/"y" before the last item into a comma so a simple split works.
    tail = re.sub(r"\s*,?\s+(?:and|y)\s+", ", ", tail, flags=re.IGNORECASE)
    items = [item.strip(" .") for item in tail.split(",")]
    items = [re.sub(r"^(?:by|por)\s+", "", item, flags=re.IGNORECASE) for item in items]
    items = [item.strip(" .") for item in items]
    items = [item for item in items if item and len(item) <= 60]
    return items


def _title_case_label(label):
    """Turn a raw extracted phrase into a display-ready segment label, e.g.
    'product type' -> 'Por Tipo de Producto' style is NOT attempted here --
    we simply title-case the phrase as extracted (works for both EN and ES
    source text) so results stay faithful to the source wording."""
    label = re.sub(r"\s+", " ", label).strip(" .:")
    if not label:
        return label
    return label[0].upper() + label[1:]


def extract_segments_from_text(text, max_segments=8):
    """
    Best-effort extraction of segmentation category names from a pasted
    report paragraph. Tries three strategies, in order:

    1. Labeled headers: "By Product Type:", "Por Aplicación:", etc. --
       collects every distinct category header found in the text.
    2. List-style sentence: "The market is segmented based on product type,
       application, source, and region." -- splits the trailing list.
    3. Line-list under a "Siguientes Segmentos:" / "Following Segments:"
       introducer -- each segment name on its own line rather than a
       comma-separated list (common in "Alcance del Informe" scope sections).

    Returns a list of segment label strings (may be empty if nothing matched).
    """
    if not text or not text.strip():
        return []

    t = text.strip()

    # Strategy 1: labeled headers (works even if headers are scattered
    # across the paragraph, e.g. multiple "By X:" occurrences). The
    # "Siguientes Segmentos:"/"Following Segments:" introducer itself can
    # incidentally match this pattern too (it's a "por ...:" phrase) --
    # filtered out here since it's the list's INTRO, not a segment.
    labeled = _LABELED_SEGMENT_RE.findall(t)
    labeled = [_title_case_label(m) for m in labeled]
    labeled = [m for m in labeled if m]
    labeled = [m for m in labeled if not re.search(r"siguientes\s+segmentos|following\s+segments", m, re.IGNORECASE)]
    if len(labeled) >= 2:
        seen = []
        for label in labeled:
            if label.lower() not in [s.lower() for s in seen]:
                seen.append(label)
        return seen[:max_segments]

    # Strategy 2: "segmented by/based on A, B, and C" list sentence.
    list_match = _SEGMENT_LIST_INTRO_RE.search(t)
    if list_match:
        items = _split_list_tail(list_match.group(1))
        items = [_title_case_label(i) for i in items]
        items = [i for i in items if i]
        if len(items) >= 2:
            return items[:max_segments]

    # Strategy 3: "... por los Siguientes Segmentos:\nAplicación\nPaís" --
    # each segment on its own line below the introducer. Stops at the first
    # blank line (once collection has started), or at a line that looks
    # like prose/data rather than a short category label (too long,
    # contains a digit, or contains a colon -- e.g. a following bullet like
    # "* Tamaño del Mercado en 2025: 0,18 MMT" must not be swept in when
    # there's no blank line separating the segment list from what follows).
    lines_match = _SEGMENT_LINES_INTRO_RE.search(t)
    if lines_match:
        tail = t[lines_match.end():]
        candidate_lines = []
        for raw_line in tail.splitlines():
            line = raw_line.strip(" -•*\t")
            if not line:
                if candidate_lines:
                    break
                continue
            if len(line) > 60 or ":" in line or "：" in line or any(ch.isdigit() for ch in line):
                break
            candidate_lines.append(_title_case_label(line))
            if len(candidate_lines) >= max_segments:
                break
        if len(candidate_lines) >= 2:
            return candidate_lines

    return []
