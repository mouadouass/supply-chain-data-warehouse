import pandas as pd

from transformations.common.cities import region_for, standardize_city


def test_villes_standardisees():
    s = pd.Series(["NADOR", "nador", " Nador ", "FÈS", "fes", "BENI MELLAL", "Lyon"])
    assert standardize_city(s).tolist() == ["Nador", "Nador", "Nador", "Fès", "Fès", "Béni Mellal", "Lyon"]


def test_ville_manquante_reste_manquante():
    assert standardize_city(pd.Series([None])).isna().all()


def test_region_deduite_de_la_ville():
    assert region_for(pd.Series(["Nador", "Oujda"])).tolist() == ["Oriental", "Oriental"]
