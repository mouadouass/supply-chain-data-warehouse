"""Valeurs invalides : négatives, impossibles, incohérentes."""
from datetime import date, timedelta


def make_negative(df, idx, rng, column):
    for i in idx:
        df.at[i, column] = -abs(df.at[i, column])


def zero_or_negative(df, idx, rng, column):
    for i in idx:
        df.at[i, column] = int(rng.choice([0, -1, -2, -3]))


def future_dates(df, idx, rng, column):
    for i in idx:
        df.at[i, column] = date(2027, int(rng.integers(1, 13)), int(rng.integers(1, 28))).isoformat()


def break_email(df, idx, rng, column):
    for i in idx:
        df.at[i, column] = str(df.at[i, column]).replace("@", "")


def arrival_before_ship(df, idx, rng):
    for i in idx:
        ship = date.fromisoformat(str(df.at[i, "ship_date"]))
        df.at[i, "actual_delivery_date"] = (ship - timedelta(days=int(rng.integers(1, 4)))).isoformat()
