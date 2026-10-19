"""Valeurs manquantes, écrites de plusieurs façons (vide, NULL, N/A)."""
EMPTY_FORMS = [None, "", "NULL", "N/A"]


def blank_values(df, idx, rng, column):
    for i in idx:
        df.at[i, column] = EMPTY_FORMS[rng.integers(len(EMPTY_FORMS))]
