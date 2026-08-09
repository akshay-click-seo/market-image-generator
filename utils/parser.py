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

NUM = r"(?:USD|US\$|\$|€|£|₹|¥)?\s*([\d,]+(?:\.\d+)?)"


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
    raw_text: str = ""

    def to_dict(self):
        return asdict(self)


def _clean_number(s):
    return float(s.replace(",", ""))


def _detect_currency(text):
    upper = text.upper()
    for sym, code in CURRENCY_SYMBOLS.items():
        if sym in upper or sym in text:
            return code
    return "USD"


def _detect_unit(text):
    lower = text.lower()
    if "mil millones" in lower or "billion" in lower or re.search(r"\bbn\b", lower):
        return "Billion"
    if "millones" in lower or "million" in lower or re.search(r"\bmn\b", lower):
        return "Million"
    return "Million"


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

    # --- CAGR: "CAGR of 9.74%" / "CAGR del 25.8%" / "growing at a CAGR of X%"
    cagr_match = re.search(
        r"CAGR[^%\d]{0,15}?([\d]+(?:[.,]\d+)?)\s*%", t, re.IGNORECASE
    )
    if not cagr_match:
        cagr_match = re.search(r"([\d]+(?:[.,]\d+)?)\s*%\s*CAGR", t, re.IGNORECASE)
    if cagr_match:
        result.cagr = float(cagr_match.group(1).replace(",", "."))

    # --- Forecast period: "during 2026-2035" / "2025-2036" / "durante el periodo ... 2026 - 2035"
    period_match = re.search(r"(20\d{2})\s*[-–—aA]{1,3}\s*(20\d{2})", t)
    if period_match:
        y1, y2 = int(period_match.group(1)), int(period_match.group(2))
        result.forecast_period = f"{y1}-{y2}"

    # --- Base year value: "reached USD 145 Million in 2025" / "alcanzo ... USD 2.4 Mil Millones en 2025"
    base_match = re.search(
        NUM + r"\s*(mil millones|millones|million|billion|bn|mn)?\s*(?:.{0,20}?)\b(?:in|en)\s+(20\d{2})",
        t, re.IGNORECASE
    )
    if base_match:
        result.start_value = _clean_number(base_match.group(1))
        result.base_year = int(base_match.group(3))
        if base_match.group(2):
            local_unit = base_match.group(2).lower()
            if local_unit in ("mil millones", "billion", "bn"):
                result.unit = "Billion"
            else:
                result.unit = "Million"

    # --- End/forecast value: "reach USD 367.3 Million by 2035" / "alcance USD 29.8 Mil Millones para 2036"
    end_match = re.search(
        NUM + r"\s*(mil millones|millones|million|billion|bn|mn)?\s*(?:.{0,20}?)\b(?:by|para|para el año|hacia)\s+(20\d{2})",
        t, re.IGNORECASE
    )
    if end_match:
        result.end_value = _clean_number(end_match.group(1))
        result.forecast_year = int(end_match.group(3))
        if end_match.group(2):
            local_unit = end_match.group(2).lower()
            if local_unit in ("mil millones", "billion", "bn"):
                result.unit = "Billion"
            else:
                result.unit = "Million"

    # --- Fallbacks: if base/end not matched via "in/by" pattern, fall back to first two
    # currency-prefixed numbers found in order of appearance.
    if result.start_value is None or result.end_value is None:
        all_nums = re.findall(NUM, t)
        if all_nums:
            nums = [_clean_number(n) for n in all_nums]
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
