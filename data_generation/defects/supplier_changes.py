"""Évolution volontaire : des fournisseurs changent de ville entre deux lots.

Ce n'est pas un défaut : c'est ce qui permet de tester l'historisation (SCD Type 2).
"""
from data_generation import config
from data_generation.utils.report import HISTORISE
from data_generation.utils.writers import read_reference


def relocate_suppliers(suppliers):
    out = suppliers.copy()
    cities = read_reference("cities.csv")["city"].tolist()
    changes = []
    for sid, new_city in config.RELOCATING_SUPPLIERS.items():
        mask = out["supplier_id"] == sid
        if not mask.any():
            continue
        old_city = out.loc[mask, "city"].iloc[0]
        if old_city == new_city:                       # il doit vraiment changer de ville
            new_city = next(c for c in cities if c != old_city)
        out.loc[mask, "city"] = new_city
        changes.append(("suppliers", f"{sid} déménage de {old_city} vers {new_city}", 1, HISTORISE))
    return out, changes
