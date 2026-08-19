"""
numfmt.py
Spanish-locale number formatting helpers.

In Spanish-format reports the roles of "." and "," are swapped compared to
English:

    English          Spanish
    180.9        ->  180,9
    10,179       ->  10.179
    20,244.03    ->  20.244,03

i.e. "." is the thousands separator and "," is the decimal separator. A
naive `.replace(".", ",")` only swaps the decimal point and leaves no
thousands separator at all (or worse, corrupts one that was never grouped
in the first place), so any value >= 1000 was rendering wrong
(e.g. "10179,00" instead of "10.179,00"). These helpers always group
thousands correctly before swapping separators.
"""


def format_es_number(value, decimals=2):
    """Format a number using Spanish conventions: '.' for thousands,
    ',' for the decimal separator. Always shows `decimals` decimal places.

    format_es_number(180.9)      -> "180,90"
    format_es_number(10179)      -> "10.179,00"
    format_es_number(20244.03)   -> "20.244,03"
    """
    if value is None:
        return ""
    # Build the English-grouped string first (e.g. "20,244.03"), then swap
    # separators using a placeholder so "," and "." never collide mid-swap.
    en = f"{value:,.{decimals}f}"
    return en.replace(",", "￼").replace(".", ",").replace("￼", ".")


def format_es_percent(value, decimals=2):
    """Format a percentage using Spanish conventions, e.g. 9.74 -> '9,74%'."""
    if value is None:
        return ""
    return f"{format_es_number(value, decimals)}%"


def format_es_number_exact(value, max_decimals=6):
    """Format a number using Spanish conventions WITHOUT rounding it away --
    preserves however many decimal digits the value actually has, instead of
    always padding/truncating to a fixed count like format_es_number() does.

    format_es_number_exact(9.873)   -> "9,873"   (NOT rounded to "9,9")
    format_es_number_exact(29.8)    -> "29,8"    (NOT padded to "29,80")
    format_es_number_exact(10179)   -> "10.179"  (whole numbers show no decimals)

    `max_decimals` is just a safety cap against floating-point noise (e.g. a
    value like 0.1 + 0.2 rendering as "0,30000000000000004") -- real report
    figures never need anywhere near that many digits, so the cap never
    truncates genuine precision in practice; trailing zeros beyond that are
    always stripped first.
    """
    if value is None:
        return ""
    en = f"{value:,.{max_decimals}f}"
    if "." in en:
        en = en.rstrip("0").rstrip(".")
    return en.replace(",", "￼").replace(".", ",").replace("￼", ".")


def format_es_percent_exact(value, max_decimals=6):
    """Percent version of format_es_number_exact(), e.g. 9.74 -> '9,74%',
    9.7 -> '9,7%' (not padded/rounded to a fixed decimal count)."""
    if value is None:
        return ""
    return f"{format_es_number_exact(value, max_decimals)}%"


# Sentinel value used by the Currency dropdown's "None" option, for reports
# whose value has no currency at all (e.g. a quantity in MMT/Toneladas with
# no price attached).
NO_CURRENCY = "None"


def has_currency(currency):
    """True if `currency` is a real currency code that should be displayed
    -- False for the NO_CURRENCY sentinel, empty string, or None."""
    return bool(currency) and currency.strip().lower() != NO_CURRENCY.lower()


def format_money_parts(currency, *parts):
    """Join a currency code with one or more value/unit strings, e.g.
    format_money_parts('USD', '29,8', 'Millones') -> 'USD 29,8 Millones'.

    If `currency` is falsy or the NO_CURRENCY sentinel, it's simply
    omitted -- the literal word "None" must never be rendered on a
    generated image, only used internally to mean "no currency"."""
    bits = [p for p in parts if p]
    if has_currency(currency):
        bits.insert(0, currency.strip())
    return " ".join(bits)


def parse_es_number(text, default=0.0):
    """Parse a Spanish- or English-formatted number string back to a float.

    Accepts whatever a user might reasonably type: '18,00' (Spanish),
    '18.00' (English), '10.179,00' (Spanish w/ thousands), '10179' (plain).
    Falls back to `default` if the text can't be parsed at all, so a typo
    never crashes the page.
    """
    if text is None:
        return default
    s = text.strip()
    if not s:
        return default
    s = s.replace(" ", "")
    has_comma = "," in s
    has_dot = "." in s
    try:
        if has_comma and has_dot:
            # whichever separator appears LAST is the decimal separator
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif has_comma:
            # single comma (or repeated -> thousands): treat the last
            # comma-group as decimal only if it looks like "18,00" (<=2
            # digits after it and just one comma); otherwise treat commas
            # as thousands separators.
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        # plain dot-only or digit-only strings parse fine as-is
        return float(s)
    except ValueError:
        return default


def es_number_input(st, label, value, decimals=2, key=None, help=None):
    """Drop-in replacement for st.number_input that displays and accepts
    Spanish-formatted numbers (comma decimal) instead of Streamlit's
    English-only number widget. Returns a float.

    Renders as a text_input pre-filled with the Spanish-formatted value
    (e.g. '18,00'); whatever the user types is parsed back to a float via
    `parse_es_number`, tolerating both comma and period input so a user
    who types '18.00' out of habit still works.

    `value` only seeds the FIRST render. If `key` already has a
    session_state entry (either from a previous render, or because calling
    code pre-set it -- e.g. an Auto-Fetch feature programmatically
    overwriting the field), that stored value is used instead and `value`
    is omitted from the st.text_input call entirely. Passing both
    unconditionally would still resolve correctly (Streamlit prefers
    session_state[key]), but it also logs a
    "widget was created with a default value but also had its value set
    via the Session State API" warning on every such rerun -- omitting it
    avoids the warning without changing behavior.
    """
    if key and key in st.session_state:
        text_value = st.text_input(label, key=key, help=help)
    else:
        default_text = format_es_number(value, decimals)
        text_value = st.text_input(label, value=default_text, key=key, help=help)
    return parse_es_number(text_value, default=value)
