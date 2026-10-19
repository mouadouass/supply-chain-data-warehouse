"""Doublons : la même ligne présente plusieurs fois."""


def exact_copies(df, idx):
    return df.loc[idx].copy()


def case_variant_copies(df, idx, column):
    """Même identifiant, mais le texte est écrit en majuscules."""
    copies = df.loc[idx].copy()
    copies[column] = copies[column].astype(str).str.upper()
    return copies
