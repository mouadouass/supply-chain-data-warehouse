import pandas as pd

from transformations.common.dates import parse_dates


def test_tous_les_formats_donnent_la_meme_date():
    s = pd.Series(["2026-10-01", "01/10/2026", "01-10-2026", "1 Oct 2026", " 1 oct 2026 "])
    assert (parse_dates(s) == pd.Timestamp("2026-10-01")).all()


def test_dates_invalides_donnent_nat():
    s = pd.Series(["31/02/2026", "abc", None, "2026-13-45", ""])
    assert parse_dates(s).isna().all()
