"""La livraison quotidienne : le plus ancien lot en attente passe dans raw/, un seul à la fois."""
from ingestion.receive_new_lot import move_next_lot


def _lot(folder, name):
    (folder / name).mkdir(parents=True)
    (folder / name / "orders.csv").write_text("x")


def test_livre_le_plus_ancien_lot_en_premier(tmp_path):
    incoming, raw = tmp_path / "incoming", tmp_path / "raw"
    raw.mkdir()
    _lot(incoming, "2026-09-03")
    _lot(incoming, "2026-09-02")
    assert move_next_lot(incoming, raw) == ("2026-09-02", 1)
    assert (raw / "2026-09-02" / "orders.csv").exists()
    assert not (incoming / "2026-09-02").exists()
    assert move_next_lot(incoming, raw) == ("2026-09-03", 0)
    assert move_next_lot(incoming, raw) == (None, 0)          # plus rien à livrer


def test_salle_d_attente_inexistante(tmp_path):
    assert move_next_lot(tmp_path / "absente", tmp_path) == (None, 0)