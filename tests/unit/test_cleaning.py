import pandas as pd

from transformations.common.cleaning import (canonicalize, clean_text, is_valid_email,
                                             normalize_name, to_integer)
from transformations.common.dedup import keep_latest, keep_versions


def test_valeurs_manquantes_sous_toutes_leurs_formes():
    s = clean_text(pd.Series(["  Sara  ", "", "NULL", "N/A", None, "a   b"]))
    assert s.tolist() == ["Sara", None, None, None, None, "a b"]


def test_noms_en_majuscules():
    assert normalize_name(pd.Series(["ALI", "EL AMRANI", "Sara", "Perrin SARL"])).tolist() == \
        ["Ali", "El Amrani", "Sara", "Perrin SARL"]


def test_fautes_de_frappe_corrigees():
    s = pd.Series(["livree", "LIVRÉE", "Livre", "annulee", "en cours", "bizarre"])
    out = canonicalize(s, ["En cours", "Expédiée", "Livrée", "Annulée"])
    assert out.tolist() == ["Livrée", "Livrée", "Livrée", "Annulée", "En cours", None]


def test_emails():
    assert is_valid_email(pd.Series(["a@b.ma", "ab.ma", None])).tolist() == [True, False, False]


def test_entiers():
    values, ok = to_integer(pd.Series(["3", "-2", "2.5", "abc", None]))
    assert ok.tolist() == [True, True, False, False, False]
    assert values.iloc[1] == -2


def _df(rows):
    return pd.DataFrame(rows, columns=["k", "batch_id", "row_number_in_file", "v"])


def test_keep_latest_garde_le_lot_le_plus_recent():
    df = _df([("A", "2026-10-01", 1, "ancien"), ("A", "2026-10-02", 1, "nouveau"),
              ("B", "2026-10-01", 1, "x"), ("B", "2026-10-01", 2, "y")])
    kept, removed = keep_latest(df, ["k"])
    assert removed == 2 and sorted(kept["v"]) == ["nouveau", "y"]


def test_keep_versions_garde_seulement_les_changements():
    df = _df([("A", "2026-10-01", 1, "Casa"), ("A", "2026-10-02", 1, "Rabat"),
              ("B", "2026-10-01", 1, "Fès"), ("B", "2026-10-02", 1, "Fès")])
    kept, removed = keep_versions(df, ["k"], ["v"])
    assert removed == 1 and len(kept) == 3
