# Génération des données

Ce dossier **simule l'entreprise** : il fabrique les fichiers sources (CSV et JSON) avec des défauts volontaires. Le pipeline Data Engineering commence à partir de `data/raw/`.

## Lancer

Depuis la racine du projet :

```text
pip install -r requirements.txt
python -m data_generation.main              # lots 1 et 2 (environ 10 secondes)
python -m data_generation.main --stress     # + un lot très défectueux
python -m pytest                            # tests
python data_generation/mock_api/app.py      # API locale des livraisons (port 8000)
```

## Ce qui est produit

| Dossier | Contenu |
|---|---|
| `data/raw/<lot>/` | Fichiers AVEC défauts (ce que le pipeline recevra) |
| `data/clean_reference/<lot>/` | Les mêmes données PARFAITES, pour vérifier le nettoyage |
| `data/ground_truth/<lot>/` | `defects_report.csv` (défauts injectés) et `tables_summary.csv` (résumé par table) |
| `data/ground_truth/story.json` | L'histoire cachée dans les données |

## Les lots

| Lot | Contenu |
|---|---|
| `2026-10-01` | Tout l'historique du 1er octobre 2024 au 30 septembre 2026 |
| `2026-10-02` | Les nouveautés du 1er octobre 2026 : nouvelles commandes, statuts qui changent, 2 fournisseurs qui déménagent, 3 nouveaux clients. Les tables de référence (clients, fournisseurs, produits, entrepôts) sont renvoyées en entier. |
| `stress_test` | Le lot 2 avec 5 fois plus de défauts, pour vérifier que le pipeline s'arrête |

## Comment c'est construit

1. `generators/` fabrique des données **propres** dans l'ordre des dépendances (fournisseurs, entrepôts, clients, produits, commandes, livraisons, stocks).
2. `generators/snapshots.py` découpe cette entreprise en deux lots.
3. `defects/` **salit** les données selon les taux de `config.py`. Chaque ligne reçoit au plus un défaut, et les doublons ne copient que des lignes propres : le rapport est donc exact.

## Les réglages

Tout se change dans `config.py` : volumes, période, taux de défauts, histoire. La `SEED` rend les résultats reproductibles.

## L'histoire cachée (à retrouver avec le dashboard)

- Les fournisseurs S004 et S011 livrent souvent en retard.
- L'entrepôt W04 (Oujda) est plus lent et se réapprovisionne plus tard.
- Les ventes explosent en novembre-décembre (Électronique) et en septembre (Bureau).
- Six produits sont souvent en rupture.
- Les fournisseurs S002 et S009 changent de ville au lot 2 (test du SCD Type 2).

## Simplifications à connaître

- Une commande « En cours » (pas encore expédiée) n'a pas de livraison.
- Une livraison est rattachée au fournisseur du produit le plus cher de la commande.
- Dans le lot 2, les statuts des anciennes commandes qui changent sont renvoyés (même `order_id`) : Silver doit garder la version la plus récente.
