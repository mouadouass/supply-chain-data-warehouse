# Supply Chain Data Warehouse & Analytics : documentation complète du projet

Ce document explique **tout le projet**, du besoin métier au dashboard : pourquoi il existe, comment il est construit, ce que fait chaque dossier, chaque étape du pipeline, les chiffres obtenus, les choix de conception et les limites.

---

## Table des matières

1. [Le projet en bref](#1-le-projet-en-bref)
2. [Le besoin métier](#2-le-besoin-métier)
3. [Les règles métier](#3-les-règles-métier)
4. [Vue d'ensemble de l'architecture](#4-vue-densemble-de-larchitecture)
5. [La stack technique](#5-la-stack-technique)
6. [Structure du projet](#6-structure-du-projet)
7. [Les données sources et leur génération](#7-les-données-sources-et-leur-génération)
8. [L'environnement Docker](#8-lenvironnement-docker)
9. [Bronze : charger sans toucher](#9-bronze--charger-sans-toucher)
10. [Silver : nettoyer et valider](#10-silver--nettoyer-et-valider)
11. [Les contrôles qualité](#11-les-contrôles-qualité)
12. [Gold : le Star Schema](#12-gold--le-star-schema)
13. [La réconciliation Silver / Gold](#13-la-réconciliation-silver--gold)
14. [L'orchestration avec Airflow](#14-lorchestration-avec-airflow)
15. [Le dashboard Power BI](#15-le-dashboard-power-bi)
16. [Les tests](#16-les-tests)
17. [Comment lancer le projet](#17-comment-lancer-le-projet)
18. [Les chiffres clés](#18-les-chiffres-clés)
19. [Les choix de conception](#19-les-choix-de-conception)
20. [Les limites et les améliorations possibles](#20-les-limites-et-les-améliorations-possibles)
21. [Problèmes rencontrés et solutions](#21-problèmes-rencontrés-et-solutions)
22. [Comment présenter le projet](#22-comment-présenter-le-projet)
23. [Glossaire](#23-glossaire)

---

## 1. Le projet en bref

**Objectif :** construire une plateforme Data Engineering complète, 100 % locale, qui transforme des données brutes et défectueuses de supply chain en un entrepôt de données fiable, alimentant un dashboard Power BI.

```text
Source simulée → 1 lot de base + 31 lots quotidiens (un livré par nuit)
      ↓
Bronze → Silver → Contrôles qualité → Gold (Star Schema) → Réconciliation → Power BI
(tout orchestré chaque nuit par Airflow, dans Docker)
```

**Ce que le projet démontre :**

| Compétence | Où la voir |
|---|---|
| Ingestion et ETL | Génération des données, Bronze, Silver |
| Qualité des données | 76 règles, quarantaine, arrêt du pipeline |
| Modélisation dimensionnelle | Star Schema, grain, clés de substitution, SCD Type 2 |
| Orchestration | DAG Airflow, relances, dépendances |
| Industrialisation | Docker Compose, tests, idempotence |
| Analytics | SQL, vues, Power BI, mesures DAX |

---

## 2. Le besoin métier

Une entreprise de distribution achète des produits à des fournisseurs, les stocke dans des entrepôts, les vend à des clients et les livre. Ses données sont dispersées dans plusieurs fichiers gérés par des équipes différentes : formats incohérents (`Nador`, `NADOR`, `nador`), dates écrites de plusieurs façons, doublons, valeurs manquantes.

**Conséquences :**
- la direction obtient plusieurs chiffres différents pour la même question ;
- personne ne sait quel fournisseur ou quel entrepôt cause les retards ;
- les ruptures de stock sont découvertes après que les clients ont été déçus.

**Le besoin réel :** une seule version fiable de la vérité, à jour et facile à consulter.

### Les utilisateurs et leurs 10 questions

| Utilisateur | Question |
|---|---|
| Direction | Q1. Quel est le chiffre d'affaires et son évolution par rapport à l'an dernier ? |
| Direction | Q2. Quelles régions et catégories rapportent le plus ? |
| Commercial | Q3. Qui sont les 10 meilleurs clients et quelle part du chiffre d'affaires représentent-ils ? |
| Commercial | Q4. Quels produits progressent ou reculent ? |
| Logistique | Q5. Quels sont le délai moyen et le taux de retard par mois ? |
| Logistique | Q6. Quel entrepôt est le plus lent ? |
| Achats | Q7. Quels fournisseurs causent le plus de retards ? |
| Achats | Q8. Quelle part du chiffre d'affaires dépend de chaque fournisseur ? |
| Stock | Q9. Quels produits sont en rupture, où, et pendant combien de jours ? |
| Stock | Q10. Quel est le stock par entrepôt et quels produits dorment ? |

Chaque graphique du dashboard répond à une de ces questions et correspond à une décision possible (renégocier un fournisseur, relever un stock de sécurité, etc.).

---

## 3. Les règles métier

Toutes les définitions sont dans `docs/business_rules.md`. Elles sont appliquées de la même façon partout (génération, nettoyage, contrôles, Gold, Power BI).

| Notion | Définition retenue |
|---|---|
| Livraison en retard | Date d'arrivée réelle postérieure à la date prévue |
| Taux de retard | Livraisons en retard divisées par livraisons arrivées |
| Délai de livraison | Jours entre l'expédition et l'arrivée réelle |
| Rupture de stock | Stock à zéro à la fin de la journée |
| Stock bas | Stock inférieur ou égal à 10 unités (rupture comprise) |
| Chiffre d'affaires | Quantité multipliée par le prix unitaire, hors taxes, hors frais de livraison, **hors commandes annulées**, en dirhams (MAD) |
| Commande annulée | Exclue du chiffre d'affaires, du nombre de commandes et des livraisons ; conservée avec son statut pour calculer le taux d'annulation |
| Livraison sans date d'arrivée | « En transit » si la date prévue n'est pas dépassée ; sinon anomalie signalée, exclue du délai moyen |
| Valeur invalide | Rejetée en quarantaine avec son motif |
| Seuil d'arrêt | Plus de 5 % de lignes rejetées sur une table : le pipeline s'arrête |
| Historisation | Ville du fournisseur, catégorie du produit, région du client (SCD Type 2) |

---

## 4. Vue d'ensemble de l'architecture

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ SIMULATION DE L'ENTREPRISE            data_generation/  (Faker)          │
│   générateurs propres → défauts injectés → 1 lot de base + 31 lots/jour  │
│   data/raw/ (lot de base)      data/incoming/ (31 lots en attente)       │
│   + data/clean_reference/ (version parfaite) + data/ground_truth/        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼  chaque nuit : receive_new_lot (incoming → raw)
 ┌──────────────────── ORCHESTRÉ PAR AIRFLOW (chaque nuit, 02:00) ───────────────────┐
 │  BRONZE → SILVER → QUALITÉ → GOLD → RÉCONCILIATION                                 │
 │  copie     propre    76 règles   Star Schema   Silver = Gold                        │
 │  brute               bloquant = arrêt                                               │
 └────────────────────────────────────────────────────────────────────────────────────┘
                                ▼
                           POWER BI  (3 pages : Ventes, Livraisons, Stocks)

Infrastructure : Docker Compose = PostgreSQL (entrepôt) + pgAdmin + base interne Airflow + Airflow
```

**Principes d'architecture :**

1. **Aucune donnée source n'est jamais modifiée.** Bronze garde la copie brute.
2. **Chaque couche a un seul rôle** : conserver (Bronze), nettoyer (Silver), modéliser (Gold).
3. **Aucune ligne n'est supprimée en silence** : les lignes invalides vont en quarantaine avec leur motif.
4. **Le pipeline se protège** : une règle qualité bloquante arrête tout avant Gold.
5. **Tout est relançable** : chaque étape donne le même résultat si on la relance (idempotence).
6. **Airflow ne contient aucune logique** : il appelle les programmes du projet dans le bon ordre.
7. **La source livre un lot par jour** : chaque nuit, le plus ancien lot en attente est livré, et seuls les lots que la base ne connaît pas sont chargés.

---

## 5. La stack technique

| Besoin | Outil | Version / détail |
|---|---|---|
| Génération et transformations | Python | 3.11 ; pandas, numpy, Faker |
| Accès à la base | psycopg2 | chargement rapide par `COPY` |
| Entrepôt de données | PostgreSQL | 16, dans Docker |
| Orchestration | Apache Airflow | 2.10.5, LocalExecutor |
| Environnement | Docker Compose | 4 services |
| Exploration de la base | pgAdmin | http://localhost:5050 |
| API simulée | Flask | pour les livraisons |
| Tests | pytest | 34 tests |
| Visualisation | Power BI Desktop | Windows, mode Import |
| Versioning | Git / GitHub | |

**Ports :**

| Service | Port sur ta machine |
|---|---|
| PostgreSQL (entrepôt) | **5433** (le 5432 est pris par un PostgreSQL Windows) |
| pgAdmin | 5050 |
| Airflow | 8080 |

Le port interne de PostgreSQL reste 5432 : les services Docker se parlent entre eux avec `postgres:5432`.

---

## 6. Structure du projet

```text
supply-chain-data-warehouse/
├── README.md
├── .env / .env.example          mots de passe (le .env ne va jamais sur GitHub)
├── .gitignore
├── docker-compose.yml           PostgreSQL + pgAdmin + base Airflow + Airflow
├── requirements.txt / pytest.ini / Makefile
│
├── docs/                        documentation
│   ├── business_questions.md    les 10 questions métier
│   ├── business_rules.md        définitions (retard, rupture, chiffre d'affaires...)
│   ├── data_dictionary.md       chaque colonne des 8 tables + défauts à injecter
│   ├── data_model.md            grain, clés, SCD Type 2
│   ├── documentation_projet.md  ce document
│   └── screenshots/             captures Airflow et Power BI
│
├── data_generation/             SIMULE L'ENTREPRISE
│   ├── config.py                volumes, période, taux de défauts, histoire, lots
│   ├── main.py                  lance toute la génération
│   ├── reference/               villes, noms, catégories et marques, transporteurs, statuts
│   ├── generators/              données propres + snapshots.py (découpage en lots)
│   ├── defects/                 injection des défauts, un fichier par type
│   ├── utils/                   seed, écriture des fichiers, rapport des défauts
│   └── mock_api/app.py          API locale des livraisons
│
├── data/
│   ├── raw/<lot>/               lots livrés, AVEC défauts (entrée du pipeline)
│   ├── incoming/<lot>/          lots quotidiens en attente de livraison
│   ├── clean_reference/<lot>/   les mêmes données PARFAITES
│   ├── ground_truth/<lot>/      rapport des défauts injectés + story.json
│   └── samples/                 petit jeu pour les tests
│
├── ingestion/                   SOURCES → BRONZE
│   ├── config.py                connexion (lue dans .env) et description des sources
│   ├── receive_new_lot.py       livre le plus ancien lot de incoming/ vers raw/
│   ├── extract.py               lecture des fichiers
│   ├── load_bronze.py           chargement et suivi des lots
│   └── batch_tracking.py        journal des lots déjà chargés
│
├── transformations/             BRONZE → SILVER → GOLD
│   ├── common/                  cleaning, dates, cities, dedup, rejects, db, runner
│   ├── customers.py ... inventory.py   une table = un module
│   ├── run_silver.py            construit Silver
│   ├── build_gold.py            construit Gold (et les vues)
│   └── run_reconciliation.py    réconcilie Silver et Gold
│
├── quality/run_quality.py       lance les 76 règles qualité
│
├── sql/
│   ├── 00_schemas.sql           crée bronze, silver, gold, audit
│   ├── bronze/                  tables brutes + index
│   ├── silver/                  tables typées, quarantaine, vérification des références
│   ├── quality/                 les règles (01 à 07)
│   ├── gold/dimensions/         dim_date, dim_customer, dim_product, dim_supplier, dim_warehouse, « Inconnu »
│   ├── gold/facts/              fact_sales, fact_delivery, fact_inventory
│   ├── reconciliation/          contrôles Silver = Gold
│   └── views/                   3 vues pour Power BI
│
├── dags/supply_chain_pipeline.py   le DAG Airflow (6 tâches)
├── docker/airflow/Dockerfile       image Airflow + environnement Python du pipeline
├── tests/                          unit, integration, data_quality
├── powerbi/                        dashboard (.pbix) et measures.md
└── scripts/, airflow/, logs/       utilitaires et dossiers montés dans Docker
```

---

## 7. Les données sources et leur génération

### 7.1 Les 8 tables sources

| Table | Une ligne représente | Clé |
|---|---|---|
| `customers` | un client (nom, type, ville, région, inscription) | customer_id |
| `suppliers` | un fournisseur (ville, pays, délai habituel) | supplier_id |
| `warehouses` | un entrepôt | warehouse_id |
| `products` | un produit du catalogue (catégorie, marque, prix) | product_id |
| `orders` | l'en-tête d'une commande (client, entrepôt, date, statut) | order_id |
| `order_items` | un produit dans une commande (quantité, prix) | order_item_id |
| `deliveries` | la livraison d'une commande expédiée (dates prévue et réelle, transporteur) | delivery_id |
| `inventory` | le stock d'un produit dans un entrepôt un jour donné | date + produit + entrepôt |

Les livraisons sont au format **JSON** (comme une source API), le reste en **CSV**.

### 7.2 Comment les données sont fabriquées

Le principe : **générer propre, puis salir**.

1. `generators/` fabrique des données parfaites, dans l'ordre des dépendances : fournisseurs, entrepôts, clients, produits, commandes et lignes, livraisons, stocks.
2. `generators/snapshots.py` découpe cette entreprise en **un lot de base et un lot par jour**.
3. `defects/` injecte les défauts selon les taux de `config.py`, lot par lot.
4. Chaque défaut injecté est compté dans `data/ground_truth/` : c'est la « vérité » que Silver devra retrouver.

La **seed** (42) rend tout reproductible : mêmes réglages, mêmes données exactes. La génération se fait **une seule fois** ; elle efface les anciens lots avant d'écrire les nouveaux.

### 7.3 Les lots

| Lot | Contenu | Où |
|---|---|---|
| `2026-09-01` | Lot de base : tout l'historique du 1er octobre 2024 au 31 août 2026 | `data/raw/` |
| `2026-09-02` à `2026-10-02` | **31 lots quotidiens**, un par jour du 1er septembre au 1er octobre | `data/incoming/` |
| `stress_test` | Copie du dernier lot quotidien avec 5 fois plus de défauts (option `--stress`) | `data/raw/` |

Un lot quotidien contient : les nouvelles commandes du jour, les commandes dont le statut change (expédiée ou livrée ce jour-là), les livraisons parties ou arrivées, les stocks du soir, et les tables de référence (clients, fournisseurs, produits, entrepôts) renvoyées en entier. Deux fournisseurs déménagent dans le dernier lot.

Un lot est nommé du lendemain des données qu'il contient. **Chaque nuit, Airflow livre le plus ancien lot de `data/incoming/` vers `data/raw/`** (tâche `receive_new_lot`), et Bronze charge uniquement les lots qu'il ne connaît pas.

### 7.4 Les défauts injectés

| Table | Défauts |
|---|---|
| customers | doublons (exacts, nom en majuscules), villes en casse différente, ville manquante, espaces parasites, e-mail invalide, dates en formats mixtes |
| suppliers | ville en casse différente, pays manquant, délai négatif, doublon |
| warehouses | ville en casse différente, espaces parasites |
| products | catégorie mal écrite, marque manquante, prix négatif ou manquant, fournisseur inexistant, doublons |
| orders | dates en formats mixtes, statut mal écrit, date dans le futur, client inexistant ou manquant, entrepôt inexistant, doublons |
| order_items | quantité nulle ou négative, prix négatif ou manquant, produit ou commande inexistants, doublons |
| deliveries | dates en formats mixtes, « Livrée » sans date d'arrivée, arrivée avant l'expédition, commande inexistante, livraison d'une commande annulée, doublons |
| inventory | date en format mixte, quantité négative, produit ou entrepôt inconnu, jours manquants, doublons |

Règles pour que le rapport soit exact : chaque ligne reçoit **au plus un** défaut de valeur, et les doublons ne copient que des lignes propres. Les taux sont réglables dans `config.py`.

### 7.5 L'histoire cachée dans les données

Les données racontent une histoire que le dashboard doit permettre de retrouver (`data/ground_truth/story.json`) :

- les fournisseurs **S004** (environ 50 % de retards) et **S011** (environ 30 %) livrent souvent en retard ;
- l'entrepôt **W04 (Oujda)** est plus lent (environ 23 % de retards contre 12 à 13 % ailleurs) ;
- les ventes **explosent en novembre-décembre**, surtout en Électronique, et en septembre pour le Bureau (rentrée) ;
- les ventes **croissent de 25 %** sur deux ans et baissent le week-end ;
- **six produits** sont souvent en rupture ;
- les fournisseurs **S002** (vers Rabat) et **S009** (vers Agadir) déménagent dans le dernier lot quotidien, pour tester l'historisation.

---

## 8. L'environnement Docker

`docker-compose.yml` démarre 4 services :

| Service | Rôle |
|---|---|
| `postgres` | L'entrepôt de données (`supply_chain_dw`) |
| `pgadmin` | Interface pour explorer la base |
| `airflow_db` | Base interne d'Airflow (ses métadonnées), séparée de l'entrepôt |
| `airflow` | Serveur web et planificateur Airflow dans un seul conteneur (version légère) |

Les mots de passe ne sont jamais dans le fichier : ils viennent du `.env` (`${...}`). Les données sont stockées dans des volumes Docker, donc conservées quand on arrête les conteneurs.

Le conteneur Airflow monte le projet dans `/opt/airflow/project` et exécute les tâches dans un **environnement Python séparé** (`/home/airflow/pipeline-venv`), pour ne pas mélanger les bibliothèques du projet avec celles d'Airflow.

---

## 9. Bronze : charger sans toucher

**Rôle :** copier les fichiers sources dans PostgreSQL, **tels quels**, défauts compris.

| Point | Détail |
|---|---|
| Tables | 8 tables `bronze.*` |
| Types | **Tout en texte**, pour qu'une valeur mal formée ne fasse jamais échouer le chargement |
| Colonnes techniques | `batch_id`, `source_file`, `row_number_in_file`, `loaded_at` |
| Chargement | `COPY` par blocs (plus de 600 000 lignes de stock en quelques secondes) |
| Nulls | Une valeur vide dans un CSV arrive comme un texte vide ; un `null` du JSON arrive comme un vrai `NULL` |
| Idempotence | `audit.batch_log` retient les lots chargés : un lot déjà chargé est ignoré |
| Options | `--lot` (un lot précis), `--reset` (vide et recharge) |

Chaque nuit, Bronze ne charge que **le nouveau lot** livré : les lots déjà chargés sont ignorés. Le lot `stress_test` n'est jamais chargé automatiquement : il faut le demander. Après les 32 lots, Bronze contient environ 953 000 lignes.

**Commande :** `python -m ingestion.load_bronze`

---

## 10. Silver : nettoyer et valider

**Rôle :** transformer Bronze en données fiables, typées et validées, avec une quarantaine pour tout ce qui est invalide.

### 10.1 Le déroulement, table par table

1. Lecture de Bronze (tous les lots).
2. **Nettoyage** (Python) : espaces, villes, dates, fautes de frappe, types.
3. **Validation ligne par ligne** : les lignes invalides vont en quarantaine avec leur motif.
4. **Déduplication.**
5. Chargement dans une table de passage `stg_*`.
6. **SQL** : vérification des références (un client, un produit, une commande doivent exister) puis insertion ; les références cassées vont aussi en quarantaine.

Silver est **reconstruit en entier** à chaque lancement, donc relançable sans risque.

### 10.2 Ce que fait le nettoyage

| Sujet | Règle |
|---|---|
| Textes | Espaces inutiles supprimés ; `''`, `NULL`, `N/A` deviennent une vraie valeur manquante |
| Villes | `NADOR`, `nador`, `Nador` deviennent `Nador` (liste de référence) |
| Dates | `2026-10-01`, `01/10/2026`, `01-10-2026`, `1 Oct 2026` deviennent `2026-10-01` (le jour vient avant le mois) |
| Fautes de frappe | `livree`, `LIVRÉE`, `Livre` deviennent `Livrée` ; idem pour les catégories |
| Noms en majuscules | `ALI` devient `Ali` |
| Valeurs manquantes facultatives | « Inconnu » (ville, pays, marque, région) ou vide (e-mail invalide) |
| Types | Dates, entiers, décimaux (2 décimales) |

### 10.3 La quarantaine

Les lignes rejetées sont dans `silver.rejected_rows` : table d'origine, **motif**, lot, fichier, numéro de ligne et **ligne originale** (en JSON). Motifs : prix négatif, quantité nulle ou négative, date dans le futur, arrivée avant l'expédition, client inexistant, produit inexistant, commande inexistante ou rejetée, etc.

Une ligne dont la commande a été rejetée est rejetée aussi (**rejet en cascade**).

### 10.4 Les tables maîtres gardent les versions

Pour les clients, fournisseurs, produits et entrepôts, Silver garde **une ligne par version** : une nouvelle ligne n'apparaît que si une valeur change d'un lot à l'autre. Un fournisseur qui déménage a donc deux lignes. C'est ce qui permet le SCD Type 2 dans Gold. Les tables de transactions gardent la version la plus récente.

### 10.5 Les résultats (après les 32 lots)

| Table | Bronze | Rejetées (valeur) | Doublons écartés | Réf. KO (cascade) | Silver |
|---|---|---|---|---|---|
| customers | 32 538 | 0 | 27 984 | 0 | 4 554 |
| suppliers | 672 | 32 | 559 | 0 | 81 |
| warehouses | 160 | 0 | 155 | 0 | 5 |
| products | 6 464 | 192 | 5 591 | 63 | 618 |
| orders | 54 620 | 542 | 4 365 | 760 | 48 953 |
| order_items | 117 705 | 2 339 | 1 165 | 4 523 | 109 678 |
| deliveries | 50 026 | 489 | 2 816 | 1 370 | 45 351 |
| inventory | 691 053 | 3 438 | 7 219 | 3 065 | 677 331 |

Au total, **16 813 lignes** sont en quarantaine. Les tables de référence sont renvoyées en entier chaque jour, avec leurs défauts aléatoires, et Silver garde chaque **version** : d'où 4 554 lignes de clients pour 1 000 clients. Gold n'en tient pas compte.

Avec le seul lot de base, le chiffre d'affaires hors annulations est de 88 524 689 MAD. Il monte dès le lot suivant, car les produits rejetés dans le lot de base (par un défaut injecté) reviennent en version correcte.

**Commande :** `python -m transformations.run_silver`

---

## 11. Les contrôles qualité

**Rôle :** vérifier Silver avant de construire Gold. Si une règle **bloquante** échoue, le programme se termine avec le code 1 et le pipeline s'arrête.

### 11.1 Les 76 règles

| Famille | Règles | Exemples |
|---|---|---|
| `Q_NULL` | 9 | identifiant vide ou NULL, ville inconnue |
| `Q_DUP` | 6 | identifiant en double, même produit deux fois dans une commande |
| `Q_FK` | 10 | commande sans client, ligne sans produit, livraison sans commande |
| `Q_RNG` | 8 | quantité ≤ 0, prix négatif, stock négatif, quantité anormale |
| `Q_DATE` | 10 | expédition avant la commande, arrivée avant l'expédition, jours manquants dans le stock |
| `Q_CNT` | 33 | aucune ligne perdue entre Bronze et Silver, taux de rejet, rejets en cascade, volume du jour |

### 11.2 Bloquant ou avertissement

| Niveau | Effet | Exemples |
|---|---|---|
| **Bloquant** | Pipeline arrêté | identifiant vide, doublon de clé, référence cassée, taux de rejet supérieur à 5 % |
| **Avertissement** | On continue, l'alerte est enregistrée | « Livrée » sans date d'arrivée, livraison d'une commande annulée, jours manquants, taux de rejet entre 1 et 5 % |

Le taux de rejet se calcule sur les **rejets de valeur uniquement** ; les rejets en cascade ont leur propre règle d'avertissement.

### 11.3 Résultats

Sur le lot de base seul, comme après les 32 lots : **76 règles, 63 OK, 13 avertissements, 0 échec bloquant.** Les avertissements sont les défauts que Silver laisse passer volontairement (livraisons « Livrée » sans date d'arrivée, commandes expédiées sans livraison, jours manquants dans les stocks) et les rejets en cascade.

Le lot `stress_test` (copie du dernier lot quotidien avec 5 fois plus de défauts) sert à **prouver l'arrêt du pipeline** : chargé seul (`--reset --lot stress_test`), il doit produire des échecs bloquants sur les taux de rejet supérieurs à 5 % et le message **PIPELINE ARRÊTÉ**. Les valeurs exactes sont à relever à l'exécution : elles n'ont pas été mesurées depuis le passage aux lots quotidiens.

Chaque exécution est enregistrée dans `audit.quality_results` : on garde l'historique de la qualité.

**Commande :** `python -m quality.run_quality`

---

## 12. Gold : le Star Schema

**Rôle :** organiser les données pour répondre facilement aux questions métier.

### 12.1 Le schéma

```text
                     dim_date
                        │
 dim_customer ──── fact_sales ──── dim_product
                        │                │
                  dim_warehouse     dim_supplier
                        │
 dim_customer ─── fact_delivery ─── dim_supplier
                        │
                  dim_warehouse

 dim_product ──── fact_inventory ──── dim_warehouse
                        │
                     dim_date
```

Les dimensions sont **partagées** entre les trois faits : on peut comparer ventes, livraisons et stocks pour un même entrepôt ou un même produit.

### 12.2 Les tables de faits et leur grain

| Fait | Une ligne = | Mesures |
|---|---|---|
| `fact_sales` | un produit vendu dans une commande | quantité, prix unitaire, montant, indicateur « annulée » |
| `fact_delivery` | une livraison (commande expédiée, non annulée) | délai, retard, indicateurs « arrivée », « en retard », « sans date d'arrivée » |
| `fact_inventory` | un produit, dans un entrepôt, un jour donné | quantité, indicateurs « rupture » et « stock bas » |

Les trois ont des natures différentes : ventes = transactionnel, livraisons = cycle de vie avec plusieurs dates, stocks = photo périodique (qui ne s'additionne pas dans le temps).

### 12.3 Les dimensions

| Dimension | Historisée (SCD Type 2) sur |
|---|---|
| `dim_date` | non : une ligne par jour de 2023 à 2028, avec année, trimestre, mois, semaine, jour, week-end, jours fériés fixes |
| `dim_customer` | la **région** |
| `dim_product` | la **catégorie** |
| `dim_supplier` | la **ville** |
| `dim_warehouse` | non (les entrepôts ne changent pas) |

### 12.4 Les clés de substitution

Chaque dimension a une clé `_key` créée par l'entrepôt, distincte de l'identifiant d'origine `_id`. Un fournisseur qui déménage a **un** `supplier_id` mais **deux** `supplier_key`.

### 12.5 Le SCD Type 2 en pratique

Exemple du fournisseur S002 :

| supplier_key | ville | start_date | end_date | is_current |
|---|---|---|---|---|
| 2 | Marrakech | 1900-01-01 | 2026-09-30 | non |
| 3 | Rabat | 2026-10-01 | 9999-12-31 | oui |

- La première version commence le 1900-01-01.
- Une nouvelle version commence au **jour des données du lot** où elle apparaît.
- `end_date` = veille de la version suivante ; `9999-12-31` pour la version actuelle.
- Seul l'attribut suivi déclenche une nouvelle version ; les autres attributs prennent la valeur la plus récente.
- Chaque ligne de fait prend la **version valable à la date de l'événement** : les ventes d'avant le 1er octobre restent rattachées à Marrakech.

### 12.6 La ligne « Inconnu »

Chaque dimension contient une ligne de clé **-1** pour qu'une référence manquante ne fasse perdre aucune vente. Les lignes rejetées en Silver n'arrivent pas dans Gold.

### 12.7 Dates multiples des livraisons

`fact_delivery` porte 4 dates : commande, expédition, arrivée prévue, arrivée réelle (-1 si pas arrivée). Elles utilisent toutes `dim_date` avec un rôle différent.

### 12.8 Les vues pour Power BI

| Vue | Contenu | Lignes |
|---|---|---|
| `vw_sales_summary` | Chiffre d'affaires par mois, catégorie, région du client, fournisseur | environ 12 000 |
| `vw_delivery_performance` | Délais et retards par mois, fournisseur, entrepôt | environ 2 300 |
| `vw_inventory_status` | État actuel de chaque produit par entrepôt : rupture, stock bas, dormant (aucune vente depuis 60 jours), normal | environ 1 000 |


### 12.9 Résultats (après les 32 lots)

| Table | Lignes |
|---|---|
| dim_date | 2 193 (2 192 jours + Inconnu) |
| dim_customer | 1 001 (1 000 + Inconnu) |
| dim_product | 201 (200 + Inconnu) |
| dim_supplier | 23 (20 fournisseurs, 22 versions, + Inconnu) |
| dim_warehouse | 6 (5 + Inconnu) |
| fact_sales | 109 678 |
| fact_delivery | 45 337 (Silver 45 351 moins 14 livraisons de commandes annulées) |
| fact_inventory | 677 331 |

Aucune ligne de fait ne pointe vers « Inconnu ».

**Gold est reconstruit en entier** à chaque lancement. Il refuse de démarrer si une règle qualité bloquante échoue (option `--skip-quality` pour contourner, utilisée par Airflow qui vient de lancer la qualité).

**Commande :** `python -m transformations.build_gold`

---

## 13. La réconciliation Silver / Gold

**Rôle :** prouver qu'**aucune ligne n'est perdue ni dupliquée** entre Silver et Gold. C'est le piège classique du Star Schema : une jointure peut gonfler les ventes sans que personne ne s'en aperçoive.

**19 contrôles**, comparant la valeur de Silver et celle de Gold :

| Famille | Contrôles |
|---|---|
| Ventes | nombre de lignes, chiffre d'affaires (avec et sans annulées), commandes distinctes, quantité, absence de doublons, chiffre d'affaires **mois par mois** |
| Livraisons | nombre, arrivées, en retard, absence de doublons |
| Stocks | nombre de lignes, quantité totale, ruptures |
| Dimensions | nombre de clients, produits, fournisseurs, entrepôts distincts ; absence de versions qui se chevauchent |

**Résultat :** 19 contrôles, 19 OK, 0 écart. Après les 32 lots :

| Contrôle | Silver | Gold |
|---|---|---|
| Chiffre d'affaires hors annulées | 96 782 247,01 | 96 782 247,01 |
| Livraisons | 45 337 | 45 337 |
| Livraisons arrivées | 44 008 | 44 008 |
| Livraisons en retard | 6 061 | 6 061 |
| Lignes de stock | 677 331 | 677 331 |

Les résultats sont gardés dans `audit.reconciliation_results`. En cas d'écart, le programme se termine avec le code 1.

**Commande :** `python -m transformations.run_reconciliation`

---

## 14. L'orchestration avec Airflow

Le DAG `supply_chain_pipeline` enchaîne **6 tâches** :

```text
receive_new_lot → load_bronze → build_silver → quality_checks → build_gold → reconciliation
```

| Tâche | Rôle | Relances |
|---|---|---|
| `receive_new_lot` | La source livre le plus ancien lot de `data/incoming/` vers `data/raw/` | 2 |
| `load_bronze` | Charge les lots que la base ne connaît pas | 2 |
| `build_silver` | Nettoie, dédoublonne, met en quarantaine | 2 |
| `quality_checks` | 76 règles ; une règle bloquante arrête le pipeline | 0 |
| `build_gold` | Reconstruit le Star Schema et les vues | 2 |
| `reconciliation` | Vérifie Silver = Gold | 0 |

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Planification | `0 2 * * *` (02h00, Africa/Casablanca) | Les chiffres de la veille sont prêts le matin |
| `catchup` | faux | Ne rejoue pas les nuits manquées : le lot de la nuit sautée est livré la nuit suivante |
| `max_active_runs` | 1 | Jamais deux exécutions en même temps |
| Relances | 2, espacées de 5 minutes | Absorbent les erreurs temporaires |
| Qualité et réconciliation | 0 relance | Un échec de contrôle n'est pas un incident temporaire |
| Délai maximal | 30 minutes par tâche | Évite les blocages |
| Alerte | `notify_failure` | Message d'erreur clair dans les logs |

**Comment Airflow sait quel lot traiter :** `receive_new_lot` prend le premier dossier de `data/incoming/` dans l'ordre alphabétique (le plus ancien) ; le dossier sert de mémoire. `load_bronze` charge ensuite uniquement les lots absents de `audit.batch_log`.

**Dépendances strictes :** si `quality_checks` échoue, `build_gold` et `reconciliation` ne s'exécutent pas (orange, « upstream_failed »). Le DAG ne contient aucune logique de données.

**Idempotence :** relancer le DAG sans nouveau lot reconstruit simplement Silver et Gold à l'identique. Quand les 31 lots sont livrés, `receive_new_lot` affiche « rien à livrer » et le pipeline rejoue l'existant, sans erreur.

**Interface** (http://localhost:8080) : liste des DAGs, vue **Graph** (vert = réussi, rouge = échec, orange = jamais lancée), **Grid** (historique), **Logs** de chaque tâche, **Clear** pour relancer une tâche, **Trigger** (▶) pour livrer et traiter un jour de plus tout de suite.

---

## 15. Le dashboard Power BI

### 15.1 Connexion

PostgreSQL, serveur `localhost:5433`, base `supply_chain_dw`, utilisateur `dw_user`, mode **Import**. Tables chargées : les 5 dimensions, les 3 faits et `vw_inventory_status`.

### 15.2 Le modèle

**15 relations** plusieurs-à-un, de la table de faits vers la dimension, filtre unique :
- `fact_sales` : date, client, produit, fournisseur, entrepôt (5) ;
- `fact_delivery` : date d'expédition (**active**), fournisseur, entrepôt, client, et 3 relations de dates **inactives** (commande, prévue, réelle) (7) ;
- `fact_inventory` : date, produit, entrepôt (3).

Les vues restent sans relation. `dim_date` est marquée comme table de dates (sans la ligne « Inconnu »), et `month_name` est triée par `month`.

### 15.3 Les mesures DAX

Toutes dans la table `_Mesures` (détail dans `powerbi/measures.md`) :

| Domaine | Mesures |
|---|---|
| Ventes | Chiffre d'affaires, Nombre de commandes, Quantité vendue, Panier moyen, Taux d'annulation, CA année précédente, Évolution vs année précédente, Part du CA |
| Livraisons | Nombre de livraisons, Livraisons arrivées, Livraisons en retard, Taux de retard, Délai moyen, Retard moyen quand en retard |
| Stocks | Dernière date de stock, Stock disponible, Produits en rupture, Jours de rupture, Taux de rupture |

Les KPIs sont des **mesures** (pas des colonnes) : ils réagissent aux filtres. Les stocks utilisent la **dernière date** de la période, car un stock ne s'additionne pas dans le temps.

### 15.4 Les 3 pages

| Page | Contenu |
|---|---|
| **Ventes** | Filtres année et mois ; chiffre d'affaires, commandes, panier moyen, taux d'annulation ; courbe du chiffre d'affaires avec année précédente ; barres par catégorie et par région ; top 10 clients avec part du chiffre d'affaires |
| **Livraisons** | Livraisons, délai moyen, taux de retard, livraisons en retard ; courbe du taux de retard ; barres par fournisseur, entrepôt et transporteur |
| **Stocks** | Stock disponible, produits en rupture, taux de rupture ; courbe des jours de rupture ; stock par entrepôt ; répartition par statut ; tableau des produits en rupture |

### 15.5 Ce que le dashboard doit montrer (après les 32 lots)

| Constat | Valeur |
|---|---|
| Chiffre d'affaires hors annulations | **96 782 247,01 MAD** (le même chiffre que la réconciliation) |
| Livraisons / arrivées / en retard | 45 337 / 44 008 / 6 061 |
| Taux de retard global | **13,8 %** |
| Fournisseur le plus en retard | S004, environ 50 % |
| Entrepôt le plus lent | Oujda, environ 23 % |
| Jours de rupture | 8 500 |
| Pic de ventes | novembre-décembre, surtout en Électronique |

Le dashboard évolue chaque nuit : après chaque exécution du pipeline, il suffit de cliquer sur **Actualiser** dans Power BI.

---

## 16. Les tests

**34 tests** (33 passent, 1 est ignoré car le petit jeu de test manque de livraisons du fournisseur S004).

| Dossier | Ce qui est testé |
|---|---|
| `tests/unit/` | Dates (tous les formats), villes, nettoyage (valeurs manquantes, fautes de frappe, e-mails), déduplication et versions ; génération : reproductibilité, identifiants uniques, références propres, dates cohérentes, histoire des fournisseurs, **rapport de défauts exact**, un lot par jour nommé du lendemain, lots quotidiens couvrant toutes les nouvelles commandes ; **livraison quotidienne** : le plus ancien lot passe de `incoming/` à `raw/`, un seul à la fois |
| `tests/data_quality/` | Silver ne viole aucune règle bloquante ; une commande sans client et une livraison avant la commande sont **détectées** (puis annulées par rollback) |
| `tests/integration/` | Le fournisseur qui déménage a deux versions aux bonnes dates (ignoré tant que le dernier lot n'est pas livré) ; une seule version actuelle par identifiant ; chaque dimension a sa ligne « Inconnu » ; la réconciliation réussit et **détecte une vente supprimée** |

Les tests qui ont besoin de la base sont ignorés automatiquement si elle n'est pas disponible.

**Commande :** `python -m pytest`

---

## 17. Comment lancer le projet

Prérequis : Docker Desktop, Python 3.11, Power BI Desktop (Windows).

```text
1. copy .env.example .env                       (puis remplis les mots de passe)
2. docker compose up -d --build                 (première fois : plusieurs minutes)
3. pip install -r requirements.txt
4. python -m data_generation.main               (UNE seule fois : lot de base + 31 lots en attente)
5. python -m ingestion.load_bronze --reset      (UNE seule fois : charge le lot de base)
6. python -m transformations.run_silver
7. python -m quality.run_quality
8. python -m transformations.build_gold
9. python -m transformations.run_reconciliation
10. Ouvre http://localhost:8080 et active le DAG supply_chain_pipeline
```

**Ensuite :** chaque nuit à 02h00, Airflow livre un lot et relance le pipeline. Pour traiter un jour de plus tout de suite, clique sur ▶ (Trigger). Après chaque exécution, clique sur **Actualiser** dans Power BI.

**Pour repartir de zéro :** `python -m data_generation.main` (efface les anciens lots), puis `python -m ingestion.load_bronze --reset`, puis les commandes 6 à 9. Le `--reset` n'est nécessaire qu'après une nouvelle génération : sans lui, Bronze ignorerait les nouveaux fichiers portant les mêmes noms de lots.

**Prouver que le pipeline s'arrête :**

```text
python -m data_generation.main --stress
python -m ingestion.load_bronze --reset --lot stress_test
python -m transformations.run_silver
python -m quality.run_quality          (échecs bloquants, PIPELINE ARRÊTÉ)
```

Pour revenir à l'état normal, relance `python -m data_generation.main`, puis `python -m ingestion.load_bronze --reset` et les commandes 6 à 9.

**Commandes Docker utiles :**

| Commande | Effet |
|---|---|
| `docker compose up -d` | Démarre tout |
| `docker compose stop` | Arrête sans rien perdre |
| `docker compose down` | Supprime les conteneurs (les données restent) |
| `docker compose down -v` | Supprime aussi les données (repart de zéro) |
| `docker compose logs -f airflow` | Suit le journal d'Airflow |

---

## 18. Les chiffres clés

| Domaine | Chiffre |
|---|---|
| Période des données | 1er octobre 2024 au 1er octobre 2026 |
| Lots | 1 lot de base + 31 lots quotidiens |
| Tables sources | 8 |
| Lignes brutes dans Bronze (32 lots) | environ 953 000 |
| Lignes en quarantaine | 16 813 |
| Règles qualité | 76 (63 OK, 13 avertissements, 0 échec) |
| Contrôles de réconciliation | 19 (tous OK) |
| Tables Gold | 5 dimensions, 3 faits, 3 vues |
| Lignes de faits | 109 678 ventes, 45 337 livraisons, 677 331 stocks |
| Chiffre d'affaires (hors annulations) | 96 782 247,01 MAD |
| Taux de retard global | 13,8 % |
| Tests | 34 (33 passent, 1 ignoré) |
| Durée du pipeline par nuit | environ une à deux minutes |

---

## 19. Les choix de conception

| Choix | Pourquoi |
|---|---|
| Bronze en texte | Un chargement ne doit jamais échouer à cause d'une valeur mal formée |
| Générer propre puis salir | On connaît exactement les défauts injectés et on peut vérifier le nettoyage |
| Quarantaine plutôt que suppression | Aucune donnée n'est perdue en silence ; chaque rejet a un motif |
| Silver et Gold reconstruits en entier | Simple, relançable, sans risque d'état incohérent |
| Silver garde les versions des tables maîtres | Nécessaire pour l'historisation SCD Type 2 |
| Taux de rejet calculé sur les rejets de valeur | Les rejets en cascade gonfleraient le taux et bloqueraient à tort |
| Règles qualité écrites en SQL | Lisibles, testables, et ce qui compte est visible |
| Contrôles qualité avant Gold, réconciliation après | Qualité des entrées, puis exactitude des sorties |
| `end_date = 9999-12-31` pour la version actuelle | Simplifie les jointures par date (`BETWEEN`) |
| Livraison rattachée au fournisseur du produit le plus cher | Simplification : une commande peut avoir plusieurs fournisseurs |
| Livraisons de commandes annulées exclues de Gold | Anomalie signalée par la qualité, hors du périmètre métier |
| Airflow sans logique | On teste chaque programme sans lancer Airflow |
| Tâches dans un environnement Python séparé | Évite les conflits de bibliothèques avec Airflow |
| Un seul conteneur Airflow | Version légère, adaptée à une machine modeste |
| Mode Import dans Power BI | Rapide pour un volume local |
| KPIs en mesures DAX | Ils réagissent aux filtres |
| Un lot par jour, livré par une tâche Airflow | La source est simulée mais se comporte comme une vraie : un nouveau lot arrive chaque jour |
| Le dossier `incoming/` sert de mémoire | Aucun fichier de configuration ne dit « traite le lot n° 5 » |
| Lots générés à l'avance, en une fois | Plus simple et plus sûr que de continuer l'histoire chaque nuit |

---

## 20. Les limites et les améliorations possibles

**Limites connues :**

- **31 lots seulement** : une fois livrés, Airflow n'a plus rien de nouveau et rejoue l'existant. Il faut régénérer pour continuer.
- **Le PC et Docker doivent être allumés à 02h00**, sinon le lot de la nuit est livré la nuit suivante.
- **Traitement par lots, pas en temps réel** : les données ont environ 24 heures de retard. Le rythme peut passer à l'heure en changeant la planification du DAG.
- **Reconstruction complète** de Silver et Gold à chaque lancement : suffisant pour ce volume, mais un chargement incrémental serait nécessaire à plus grande échelle.
- **Tables de référence renvoyées chaque jour avec leurs défauts** : Silver garde donc beaucoup de versions (4 554 lignes de clients), que Gold ne conserve pas.
- **Les clés de substitution sont recalculées** à chaque reconstruction de Gold (les faits sont reconstruits avec, donc la cohérence est préservée).
- **Données synthétiques** : plus propres et plus régulières qu'une vraie entreprise.
- **Jours fériés** : seules les fêtes à date fixe sont incluses.
- **Alerte d'échec** : un message dans les logs ; pas encore d'e-mail ni de Slack.
- **Airflow** : un seul conteneur (serveur web et planificateur ensemble), à séparer en production.
- **Stock bas à 10 unités** : seuil unique, qui classe beaucoup de produits à faible rotation en « stock bas ».
- **La livraison quotidienne n'a été testée qu'en dehors de Docker** : sous Windows, le déplacement de dossiers dans le projet monté peut être bloqué par les droits d'accès.
- **Le lot `stress_test`** n'a pas été re-mesuré depuis le passage aux lots quotidiens.
- **Pas d'intégration continue** (CI) sur GitHub.

**Améliorations possibles :**

1. Chargement incrémental (dernier lot seulement) et SCD Type 2 incrémental.
2. Alertes par e-mail ou Slack dans `notify_failure`.
3. Génération automatique de nouveaux lots quand la salle d'attente est vide.
4. Alimenter Bronze depuis la mini-API au lieu des fichiers.
5. Seuils de stock bas par produit.
6. Dimension `dim_carrier` pour les transporteurs.
7. Suivi de la qualité dans Power BI (page lisant `audit.quality_results`).
8. Passage à dbt pour les transformations SQL.
9. CI GitHub (tests et lint à chaque commit).
10. Streaming (Kafka) si un besoin temps réel apparaissait.

---

## 21. Problèmes rencontrés et solutions

| Problème | Cause | Solution |
|---|---|---|
| `UnicodeDecodeError` à la connexion Python | Un PostgreSQL installé sur Windows occupait aussi le port 5432 ; Python parlait au mauvais serveur | Docker sur le port **5433** (`POSTGRES_PORT=5433` dans `.env`) |
| `password authentication failed` | Le volume gardait l'ancien utilisateur de la première création | `docker compose down -v` puis `up -d` |
| pgAdmin ne trouve pas la base | `localhost` désigne pgAdmin lui-même dans Docker | Serveur `postgres`, port `5432` |
| `No module named quality.run_quality` | Le fichier était dans un dossier `quality` imbriqué | Déplacer les fichiers au bon niveau |
| `docker compose config` : `volumes.airflow additional properties` | Les services avaient été collés après la section `volumes:` | Placer `volumes:` en dernier |
| Règle `Q_DATE_001` en échec | Les livraisons de commandes annulées (anomalie injectée) avaient des dates sans rapport | Exclure les commandes annulées de la règle (déjà signalées par `Q_DATE_007`) |
| Silver plante sur le lot de stress | Le nom `stress_test` n'est pas une date | Fonction `batch_date` avec une date de repli |
| Prise en charge du chiffrement (Power BI) | PostgreSQL local sans SSL | Accepter la connexion non chiffrée (elle reste sur la machine) |
| Ligne « Inconnu » dans `dim_date` | `full_date` vide empêche de marquer la table de dates | Supprimer les vides dans Power Query |
| Relations créées automatiquement par Power BI | Détection par noms de colonnes identiques | Tout supprimer et recréer les 15 relations |
| `PermissionError: Accès refusé` à la génération | OneDrive ou l'Explorateur tient un ancien dossier de `data\raw` | `shutil.rmtree(child, ignore_errors=True)` dans `_clean_outputs` |
| Power BI : « référence cyclique » sur `dim_warehouse` | Requête devenue circulaire | Réécrire la requête dans l'Éditeur avancé (PostgreSQL, schéma `gold`, table `dim_warehouse`) |
| Les chiffres ne changent pas après une nouvelle génération | Bronze ignore les lots déjà chargés (mêmes noms) | `python -m ingestion.load_bronze --reset` une fois |

---

## 22. Comment présenter le projet

**En une phrase :**

> « J'ai construit un pipeline Data Engineering de bout en bout pour une plateforme Supply Chain : ingestion de données volontairement défectueuses, architecture Bronze, Silver, Gold, 76 contrôles qualité qui bloquent le pipeline, Star Schema avec historisation SCD Type 2, réconciliation Silver et Gold, orchestration Airflow et dashboard Power BI. »

**Commence par le problème, pas par les outils :**

> « L'entreprise avait des données dispersées et peu fiables. J'ai conçu une plateforme qui centralise, nettoie et contrôle ces données, les organise dans un entrepôt analytique et alimente un tableau de bord pour suivre les ventes, les livraisons et les stocks. Le tout tourne automatiquement chaque nuit. »

**Questions fréquentes :**

| Question | Réponse |
|---|---|
| Pourquoi trois couches ? | Bronze garde l'original, Silver rend les données fiables, Gold les prépare à l'analyse. Chaque couche a un seul rôle. |
| C'est quoi le grain ? | Ce que représente une ligne d'une table de faits. Ex. : un produit vendu dans une commande. On le fixe avant de construire la table. |
| Pourquoi des clés de substitution ? | Pour distinguer les versions d'une même entité (SCD Type 2), et ne pas dépendre des identifiants source. |
| Comment gères-tu l'historique ? | SCD Type 2 : une nouvelle ligne avec dates de validité quand un attribut suivi change. Les ventes gardent l'ancienne valeur. |
| Que se passe-t-il si les données sont mauvaises ? | Les lignes invalides vont en quarantaine ; si le taux dépasse 5 %, le pipeline s'arrête avant Gold. |
| Comment prouves-tu que les chiffres sont justes ? | La réconciliation compare Silver et Gold (lignes, chiffre d'affaires, par mois) : 19 contrôles à zéro écart. |
| Pourquoi des données synthétiques ? | Je contrôle les défauts injectés et je peux vérifier que mon nettoyage les retrouve exactement. |
| Est-ce du temps réel ? | Non, c'est du batch quotidien : les besoins tolèrent un jour de délai. On peut passer à l'heure, et pour des alertes en direct il faudrait du streaming. |
| Qu'est-ce que l'idempotence ? | Relancer une étape donne le même résultat, sans doublons. C'est ce qui rend les relances d'Airflow sans risque. |
| Comment Airflow sait-il quel lot traiter ? | `receive_new_lot` livre le plus ancien dossier de `incoming/` ; `load_bronze` charge seulement les lots absents de `audit.batch_log`. Aucun compteur n'est nécessaire. |
| Quelles sont les limites ? | Batch, reconstruction complète, données synthétiques, alertes limitées aux logs (voir section 20). |

---

## 23. Glossaire

| Terme | Définition |
|---|---|
| **Supply chain** | La chaîne qui amène un produit du fournisseur au client |
| **Data Warehouse (entrepôt)** | Base de données organisée pour l'analyse, pas pour la saisie quotidienne |
| **Bronze / Silver / Gold** | Données brutes / nettoyées / prêtes pour l'analyse |
| **ETL** | Extraire, transformer, charger |
| **Star Schema** | Une table de faits au centre, des dimensions autour |
| **Table de faits** | Les événements mesurables (ventes, livraisons, stocks) |
| **Dimension** | Le contexte : qui, quoi, où, quand |
| **Grain** | Ce que représente une ligne d'une table de faits |
| **Clé de substitution** | Numéro créé par l'entrepôt (`_key`), distinct de l'identifiant source (`_id`) |
| **SCD Type 2** | Historisation : une nouvelle ligne à chaque changement d'un attribut suivi |
| **Dimension dégénérée** | Un identifiant conservé dans le fait, sans dimension propre (ex. `order_id`) |
| **Quarantaine** | Table où vont les lignes invalides, avec leur motif |
| **Idempotence** | Relancer donne le même résultat, sans doublons |
| **Réconciliation** | Vérifier que deux couches contiennent les mêmes totaux |
| **DAG** | Graphe de tâches Airflow, avec leur ordre |
| **Batch** | Traitement par lots, à intervalle régulier |
| **Backfill** | Rejouer l'historique |
| **Mesure DAX** | Calcul Power BI qui réagit aux filtres |
| **KPI** | Indicateur clé de performance |
| **Seed** | Graine aléatoire qui rend les données reproductibles |
| **Volume Docker** | Espace de stockage qui survit à l'arrêt des conteneurs |
| **Lot** | Un paquet de fichiers livré à une date (un fichier par table), nommé du lendemain des données qu'il contient |
| **Salle d'attente (`incoming/`)** | Dossier des lots quotidiens pas encore livrés ; Airflow en livre un par nuit |
