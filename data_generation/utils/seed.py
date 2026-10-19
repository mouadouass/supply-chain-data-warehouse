"""Rend la génération reproductible : même seed = mêmes données."""
import random
import zlib

import numpy as np
from faker import Faker


def make_rng(seed, name=""):
    """Un générateur aléatoire propre à chaque composant (clients, commandes...).
    Changer un composant ne modifie pas les autres."""
    return np.random.default_rng([seed, zlib.crc32(name.encode("utf-8"))])


def make_faker(seed, name="", locale="fr_FR"):
    fake = Faker(locale)
    fake.seed_instance(seed + zlib.crc32(name.encode("utf-8")) % 100_000)
    return fake


def set_global_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
