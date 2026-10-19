"""Clients : qui achète, et où."""
import unicodedata

import numpy as np
import pandas as pd

from data_generation import config
from data_generation.utils.writers import read_reference

EMAIL_DOMAINS = ["gmail.com", "hotmail.com", "yahoo.fr", "outlook.com"]


def _slug(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "." for c in text.lower()).strip(".")


def generate_customers(rng, fake, n=None):
    n = n or config.N_CUSTOMERS
    cities = read_reference("cities.csv")
    names = read_reference("names.csv")
    first = names.loc[names["kind"] == "first_name", "value"].tolist()
    last = names.loc[names["kind"] == "last_name", "value"].tolist()

    city_idx = rng.choice(len(cities), size=n, p=cities["weight"] / cities["weight"].sum())
    types = rng.choice(["Particulier", "Entreprise"], size=n, p=[0.85, 0.15])

    # Inscriptions étalées dans le temps ; les derniers clients s'inscrivent le jour du lot 2
    span = (config.END_DATE - config.CUSTOMER_REG_START).days + 1
    reg = pd.Timestamp(config.CUSTOMER_REG_START) + pd.to_timedelta(rng.integers(0, span, n), unit="D")
    reg = pd.Series(reg)
    reg.iloc[n - config.NEW_CUSTOMERS_LOT_2:] = pd.Timestamp(config.NEXT_DAY)

    rows = []
    for i in range(n):
        if types[i] == "Entreprise":
            name = fake.company()
            email = f"contact@{_slug(name.split()[0])}.ma"
        else:
            f, l = first[rng.integers(len(first))], last[rng.integers(len(last))]
            name = f"{f} {l}"
            email = f"{_slug(f)}.{_slug(l)}{rng.integers(1, 99)}@{EMAIL_DOMAINS[rng.integers(4)]}"
        c = cities.iloc[city_idx[i]]
        rows.append((f"C{i + 1:05d}", name, types[i], email, c["city"], c["region"], reg.iloc[i]))
    df = pd.DataFrame(rows, columns=config.COLUMNS["customers"])
    df["registration_date"] = pd.to_datetime(df["registration_date"])
    return df
