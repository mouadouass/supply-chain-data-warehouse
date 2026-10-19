# Supply Chain Data Warehouse & Analytics

Plateforme Data Engineering complète, 100 % locale : des données de supply chain brutes et défectueuses sont chargées, nettoyées, contrôlées et modélisées en entrepôt de données, puis affichées dans un dashboard Power BI. Un pipeline Airflow traite un nouveau lot de données chaque nuit.

## Le problème

Une entreprise de distribution achète des produits à des fournisseurs, les stocke dans des entrepôts, les vend à des clients et les livre. Ses données sont dispersées dans plusieurs fichiers, avec des formats incohérents, des doublons et des valeurs manquantes.

Conséquences : la direction obtient plusieurs chiffres pour la même question, personne ne sait quel fournisseur ou quel entrepôt cause les retards, et les ruptures de stock sont découvertes trop tard.

## L'objectif

Construire **une seule version fiable de la vérité** : centraliser, nettoyer, contrôler et organiser les données, puis les mettre à disposition des responsables. Le dashboard répond à 10 questions métier ([`docs/business_questions.md`](docs/business_questions.md)).

## L'architecture

```text
 Source simulée (Python, Faker)  →  1 lot de base + 31 lots quotidiens
          │                                    │
     data/raw/  ◄───── receive_new_lot ────  data/incoming/
          │             (un lot par nuit)
          ▼
 ┌─────────────── Orchestré par Airflow, chaque nuit à 02h00 ───────────────┐
 │  Bronze → Silver → Contrôle qualité → Gold → Réconciliation              │
 │  (brut)   (propre)  (76 règles)       (étoile) (Silver = Gold)           │
 └───────────────────────────────────────────────────────────────────────────┘
          ▼
      Power BI (Ventes, Livraisons, Stocks)
```

Tout tourne localement dans Docker, sans cloud. C'est un traitement **par lots quotidien**, pas du temps réel.

## Les couches

| Couche | Rôle |
|---|---|
| Bronze | Copie brute, tout en texte, avec l'origine de chaque ligne |
| Silver | Données nettoyées et typées ; les lignes invalides vont en quarantaine avec leur motif |
| Qualité | 76 règles SQL ; une règle bloquante en échec arrête le pipeline avant Gold |
| Gold | Star Schema : 5 dimensions, 3 tables de faits, historisation SCD Type 2 |
| Réconciliation | 19 contrôles : Silver et Gold donnent les mêmes chiffres |

## Le modèle de données

| Table de faits | Une ligne représente |
|---|---|
| `fact_sales` | un produit vendu dans une commande |
| `fact_delivery` | une livraison |
| `fact_inventory` | un produit, dans un entrepôt, un jour donné |

Dimensions : `dim_date`, `dim_customer` (historisée sur la région), `dim_product` (sur la catégorie), `dim_supplier` (sur la ville), `dim_warehouse`. Détails dans [`docs/data_model.md`](docs/data_model.md).

## Les technologies

Python (pandas, Faker), PostgreSQL 16, Apache Airflow 2.10, Docker Compose, Power BI, pytest.

## Les points forts

- Données générées avec des défauts volontaires, et un rapport de vérité pour vérifier le nettoyage
- Livraison quotidienne simulée : un nouveau lot chaque nuit
- Quarantaine des lignes rejetées, aucune ligne supprimée en silence
- 76 contrôles qualité bloquants ou en avertissement, avec historique
- Star Schema avec grain défini et historisation SCD Type 2
- Réconciliation entre les couches
- Pipeline idempotent, relances automatiques, arrêt avant Gold si la qualité échoue
- 34 tests automatisés

## Le dashboard

| Page | Contenu |
|---|---|
| Ventes | Chiffre d'affaires et évolution, commandes, panier moyen, catégories, régions, top 10 clients |
| Livraisons | Délai moyen, taux de retard par mois, fournisseur, entrepôt et transporteur |
| Stocks | Stock disponible, ruptures, stock par entrepôt, produits en rupture |

## Captures

![Pipeline Airflow](docs/screenshots/airflow_dag.png)
![Page Ventes](docs/screenshots/powerbi_ventes.png)
![Page Livraisons](docs/screenshots/powerbi_livraisons.png)
![Page Stocks](docs/screenshots/powerbi_stocks.png)

## Résultats clés (après les 31 lots)

| Indicateur | Valeur |
|---|---|
| Chiffre d'affaires hors annulations | 96 782 247,01 MAD |
| Livraisons / arrivées / en retard | 45 337 / 44 008 / 6 061 |
| Taux de retard global | 13,8 % |
| Contrôles qualité | 76 règles, 0 échec bloquant |
| Réconciliation Silver / Gold | 19 contrôles sur 19 |

## Documentation

| Document | Contenu |
|---|---|
| [`docs/documentation_projet.md`](docs/documentation_projet.md) | Explication complète du projet |
| [`docs/business_rules.md`](docs/business_rules.md) | Définitions métier (retard, rupture, chiffre d'affaires...) |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Colonnes des 8 tables et défauts injectés |
| [`docs/data_model.md`](docs/data_model.md) | Grain, clés, SCD Type 2 |
| [`powerbi/measures.md`](powerbi/measures.md) | Mesures DAX |

## Structure du projet

| Dossier | Contenu |
|---|---|
| `data_generation/` | Génération des données avec Faker |
| `data/` | `raw/` (lots livrés), `incoming/` (lots en attente), `clean_reference/`, `ground_truth/` |
| `ingestion/` | Livraison des lots et chargement dans Bronze |
| `transformations/` | Silver, Gold et réconciliation |
| `quality/` | Les contrôles qualité |
| `sql/` | Schémas, règles, dimensions, faits, vues |
| `dags/` | Le DAG Airflow |
| `tests/` | Tests unitaires, d'intégration et de qualité |
| `powerbi/` | Dashboard et mesures |

## Comment lancer le projet

Prérequis : Docker Desktop, Python 3.11, Power BI Desktop (Windows).

```text
copy .env.example .env                        (puis remplis les mots de passe)
docker compose up -d --build
pip install -r requirements.txt
python -m data_generation.main                (une seule fois)
python -m ingestion.load_bronze --reset
python -m transformations.run_silver
python -m quality.run_quality
python -m transformations.build_gold
python -m transformations.run_reconciliation
```

Ouvre ensuite Airflow sur http://localhost:8080 et active le DAG `supply_chain_pipeline`.

**Chaque nuit à 02h00**, Airflow livre le prochain lot de `data/incoming/` vers `data/raw/`, puis enchaîne le chargement, le nettoyage, les contrôles, Gold et la réconciliation. Pour traiter un jour de plus tout de suite, clique sur le bouton ▶ du DAG.

Dans Power BI : PostgreSQL, serveur `localhost:5433`, base `supply_chain_dw`, puis ouvre `powerbi/supply_chain_dashboard.pbix` et clique sur **Actualiser**.

Tests : `python -m pytest`

## Avancement

- [x] Cadrage métier
- [x] Dictionnaire de données
- [x] Génération des données
- [x] Base PostgreSQL et Docker
- [x] Couche Bronze
- [x] Couche Silver
- [x] Contrôles qualité
- [x] Couche Gold (Star Schema)
- [x] SCD Type 2
- [x] Réconciliation
- [x] Orchestration Airflow
- [x] Livraison quotidienne des lots
- [x] Dashboard Power BI

## Auteur

*OUASS MOUAD*