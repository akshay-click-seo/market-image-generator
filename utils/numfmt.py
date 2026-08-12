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
