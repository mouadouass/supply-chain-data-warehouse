"""Lance toute la génération des données, dans le bon ordre.

Utilisation (depuis la racine du projet) :
    python -m data_generation.main            # lot de base + un lot par jour
    python -m data_generation.main --stress   # + un lot très défectueux
"""
import argparse
import json
import shutil
import time

from data_generation import config
from data_generation.defects.inject import inject_lot
from data_generation.generators.customers import generate_customers
from data_generation.generators.deliveries import generate_deliveries
from data_generation.generators.inventory import simulate_inventory
from data_generation.generators.orders import generate_orders
from data_generation.generators.products import generate_products
from data_generation.generators.snapshots import build_lots
from data_generation.generators.suppliers import generate_suppliers
from data_generation.generators.warehouses import generate_warehouses
from data_generation.utils.report import DefectReport
from data_generation.utils.seed import make_faker, make_rng
from data_generation.utils.writers import write_lot


def build_world(seed=config.SEED, n_customers=None, n_products=None, n_orders=None):
    """Fabrique l'entreprise complète, PROPRE, dans l'ordre des dépendances."""
    fake = make_faker(seed)
    customers = generate_customers(make_rng(seed, "customers"), fake, n_customers)
    suppliers = generate_suppliers(make_rng(seed, "suppliers"), fake)
    warehouses = generate_warehouses(make_rng(seed, "warehouses"))
    products = generate_products(make_rng(seed, "products"), suppliers, n_products)
    orders, items = generate_orders(make_rng(seed, "orders"), customers, products, warehouses, n_orders)
    deliveries = generate_deliveries(make_rng(seed, "deliveries"), orders, items, products, suppliers)
    inventory, prone = simulate_inventory(make_rng(seed, "inventory"), orders, items, products,
                                          suppliers, warehouses)
    return {"customers": customers, "suppliers": suppliers, "warehouses": warehouses,
            "products": products, "orders": orders, "items": items,
            "deliveries": deliveries, "inventory": inventory, "stockout_prone": prone}


def write_story(world):
    """Les 'secrets' cachés dans les données : à retrouver avec le dashboard."""
    story = {"fournisseurs_souvent_en_retard": config.STORY["late_suppliers"],
             "entrepot_lent": config.STORY["slow_warehouse"],
             "produits_souvent_en_rupture": world["stockout_prone"],
             "fournisseurs_qui_demenagent_au_dernier_lot": config.RELOCATING_SUPPLIERS,
             "pic_de_ventes": "novembre-décembre (surtout Électronique), rentrée en septembre (Bureau)",
             "retards_plus_frequents": "novembre-décembre"}
    config.TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    (config.TRUTH_DIR / "story.json").write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean_outputs():
    """Repart de zéro : supprime les anciens lots (raw, incoming, clean_reference, ground_truth)."""
    for folder in (config.RAW_DIR, config.INCOMING_DIR, config.CLEAN_DIR, config.TRUTH_DIR):
        if folder.exists():
            for child in folder.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)


def _publish(lot, tables, events, target_dir, multiplier=1.0):
    """Écrit la version parfaite, salit les données, écrit les fichiers et le rapport des défauts."""
    write_lot(tables, config.CLEAN_DIR / lot)
    report = DefectReport(lot)
    for table, description, count, treatment in events:
        report.add(table, description, count, treatment)
    write_lot(inject_lot(tables, report, lot, multiplier), target_dir / lot)
    report.write(config.TRUTH_DIR / lot)
    return report


def run(stress=False):
    t0 = time.time()
    print("1/4 Génération des données propres...")
    world = build_world()
    print("2/4 Découpage en un lot de base et un lot par jour...")
    base, dailies = build_lots(world)

    print("3/4 Injection des défauts et écriture des fichiers...")
    _clean_outputs()
    _publish(config.BASE_LOT, base, [], config.RAW_DIR).print_summary()
    for label, tables, events in dailies:
        _publish(label, tables, events, config.INCOMING_DIR)
    print(f"\n{len(dailies)} lots quotidiens en attente dans data/incoming/ "
          f"({dailies[0][0]} à {dailies[-1][0]}). Airflow en livre un par nuit.")

    if stress:
        _publish(config.STRESS_LOT, dailies[-1][1], [], config.RAW_DIR,
                 config.STRESS_MULTIPLIER).print_summary()

    print("4/4 Histoire cachée dans les données...")
    write_story(world)
    print(f"\nTerminé en {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stress", action="store_true", help="génère aussi un lot très défectueux")
    run(parser.parse_args().stress)