"""Unifie les formats de dates : 2026-10-01, 01/10/2026, 01-10-2026, 1 Oct 2026."""
import re

import pandas as pd

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DMY = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")      # jour avant mois
_TEXT = re.compile(r"^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})$")


def _parse_one(value):
    if value is None or pd.isna(value):
        return pd.NaT
    v = str(value).strip()
    try:
        if m := _ISO.match(v):
            y, mo, d = map(int, m.groups())
        elif m := _DMY.match(v):
            d, mo, y = map(int, m.groups())
        elif m := _TEXT.match(v):
            d, y = int(m.group(1)), int(m.group(3))
            mo = MONTHS[m.group(2).lower()]
        else:
            return pd.NaT
        return pd.Timestamp(year=y, month=mo, day=d)
    except (ValueError, KeyError):
        return pd.NaT


def parse_dates(series):
    """Retourne des dates ; NaT quand la valeur n'est pas une date valide."""
    return pd.to_datetime(pd.Series([_parse_one(v) for v in series], index=series.index))
