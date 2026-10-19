"""Simule la livraison quotidienne de la source : prend le prochain lot en attente dans
data/incoming/ et le dépose dans data/raw/, où Bronze ira le chercher.

    python -m ingestion.receive_new_lot
"""
import shutil

from ingestion import config


def move_next_lot(incoming_dir=None, raw_dir=None):
    """Déplace le plus ancien lot en attente. Retourne (nom du lot, lots restants) ou (None, 0)."""
    incoming_dir = incoming_dir or config.INCOMING_DIR
    raw_dir = raw_dir or config.RAW_DIR
    waiting = sorted(p for p in incoming_dir.iterdir() if p.is_dir()) if incoming_dir.exists() else []
    if not waiting:
        return None, 0
    lot = waiting[0]
    target = raw_dir / lot.name
    if target.exists():                      # déjà livré : on retire simplement la copie en attente
        shutil.rmtree(lot)
    else:
        shutil.move(str(lot), str(target))
    return lot.name, len(waiting) - 1


def main():
    lot, remaining = move_next_lot()
    if lot is None:
        print("Aucun nouveau lot en attente : rien à livrer aujourd'hui.")
    else:
        print(f"Lot livré : {lot} ({remaining} lots encore en attente)")


if __name__ == "__main__":
    main()