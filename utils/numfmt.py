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
    """
    default_text = format_es_number(value, decimals)
    text_value = st.text_input(label, value=default_text, key=key, help=help)
    return parse_es_number(text_value, default=value)
