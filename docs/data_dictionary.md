# Dictionnaire de données

Ce document décrit les huit tables sources : ce que contient chaque colonne, son type et ses règles. Il sert de référence pour écrire les générateurs, le nettoyage et les contrôles qualité.

Il se termine par la liste des défauts à injecter dans chaque table.

## 1. Conventions

| Sujet | Règle |
|---|---|
| Types utilisés | texte, entier, décimal, date, booléen |
| Type dans Bronze | Tout est chargé en texte, sans conversion |
| Type dans Silver et Gold | Les types ci-dessous s'appliquent |
| Date | Format 2026-10-01 en Silver et Gold (les sources peuvent contenir d'autres formats) |
| Montants | Dirham marocain (MAD), deux décimales |
| Obligatoire | « Oui » = la valeur ne peut pas être vide en Silver |
| Clé primaire | Identifiant unique de la ligne |
| Langue des noms | Noms de tables et de colonnes en anglais, en minuscules avec underscores |
| Période des données | Du 1er octobre 2024 au 1er octobre 2026 |
| Lots | 1 lot de base (données jusqu'au 31 août 2026) + 31 lots quotidiens (du 1er septembre au 1er octobre 2026) |

### Format des identifiants

| Table | Format | Exemple |
|---|---|---|
| customers | C + 5 chiffres | C00012 |
| suppliers | S + 3 chiffres | S001 |
| warehouses | W + 2 chiffres | W03 |
| products | P + 4 chiffres | P0087 |
| orders | O + 6 chiffres | O001001 |
| order_items | OI + 7 chiffres | OI0003054 |
| deliveries | D + 6 chiffres | D001001 |
| inventory | pas d'identifiant propre, clé composée | voir la table |

## 2. Vue d'ensemble

| Table | Une ligne représente | Clé primaire | Dépend de | Volume indicatif |
|---|---|---|---|---|
| customers | un client | customer_id | rien | 1 000 |
| suppliers | un fournisseur | supplier_id | rien | 20 |
| warehouses | un entrepôt | warehouse_id | rien | 5 |
| products | un produit du catalogue | product_id | suppliers | 200 |
| orders | une commande (en-tête) | order_id | customers, warehouses | 50 000 |
| order_items | un produit dans une commande | order_item_id | orders, products | environ 120 000 |
| deliveries | la livraison d'une commande expédiée | delivery_id | orders, warehouses, suppliers | environ 45 000 |
| inventory | le stock d'un produit dans un entrepôt un jour donné | snapshot_date + product_id + warehouse_id | products, warehouses | jusqu'à 730 000 |

Pour inventory, le volume peut être réduit en ne gardant que certains produits par entrepôt.

## 3. Détail des tables

### 3.1 customers

Qui achète, et où.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| customer_id | texte | Identifiant du client | Oui | Unique, format C00000 |
| customer_name | texte | Nom du client | Oui | Non vide |
| customer_type | texte | Particulier ou Entreprise | Oui | Valeur dans la liste autorisée |
| email | texte | Adresse e-mail | Non | Contient un @ si renseignée |
| city | texte | Ville du client | Non | Ville de la liste de référence, standardisée |
| region | texte | Région du client | Non | Déduite de la ville |
| registration_date | date | Date d'inscription | Oui | Date valide, pas dans le futur |

### 3.2 suppliers

Qui fournit les produits.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| supplier_id | texte | Identifiant du fournisseur | Oui | Unique, format S000 |
| supplier_name | texte | Nom de la société | Oui | Non vide |
| city | texte | Ville du fournisseur | Oui | Ville de la liste de référence. Cet attribut est historisé (SCD Type 2). |
| country | texte | Pays | Oui | Non vide |
| standard_lead_time_days | entier | Délai habituel de livraison annoncé | Oui | Supérieur ou égal à 0 |

### 3.3 warehouses

Où la marchandise est stockée.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| warehouse_id | texte | Identifiant de l'entrepôt | Oui | Unique, format W00 |
| warehouse_name | texte | Nom de l'entrepôt | Oui | Non vide |
| city | texte | Ville | Oui | Ville de la liste de référence |
| region | texte | Région | Oui | Déduite de la ville |
| capacity_units | entier | Capacité maximale en unités | Oui | Strictement positif |

### 3.4 products

Ce que l'entreprise vend.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| product_id | texte | Identifiant du produit | Oui | Unique, format P0000 |
| product_name | texte | Nom du produit | Oui | Non vide |
| category | texte | Catégorie | Oui | Valeur dans la liste autorisée. Historisée (SCD Type 2). |
| brand | texte | Marque | Non | Cohérente avec la catégorie |
| unit_price | décimal | Prix catalogue en MAD | Oui | Supérieur ou égal à 0 |
| supplier_id | texte | Fournisseur du produit | Oui | Doit exister dans suppliers |
| created_date | date | Date d'ajout au catalogue | Oui | Date valide |

### 3.5 orders

L'en-tête de chaque commande.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| order_id | texte | Identifiant de la commande | Oui | Unique, format O000000 |
| customer_id | texte | Client qui commande | Oui | Doit exister dans customers |
| warehouse_id | texte | Entrepôt qui expédie | Oui | Doit exister dans warehouses |
| order_date | date | Date de la commande | Oui | Date valide, dans la période, pas dans le futur |
| status | texte | État de la commande | Oui | En cours, Expédiée, Livrée ou Annulée |

### 3.6 order_items

Les lignes de chaque commande. C'est le cœur de l'activité.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| order_item_id | texte | Identifiant de la ligne | Oui | Unique, format OI0000000 |
| order_id | texte | Commande concernée | Oui | Doit exister dans orders |
| product_id | texte | Produit vendu | Oui | Doit exister dans products |
| quantity | entier | Quantité vendue | Oui | Strictement supérieure à 0 |
| unit_price | décimal | Prix unitaire payé en MAD | Oui | Supérieur ou égal à 0, proche du prix catalogue |

Le montant d'une ligne (quantité multipliée par prix unitaire) n'est pas une colonne source. Il est calculé plus tard dans la couche Gold.

### 3.6 bis. Une commande contient combien de lignes ?

Une commande contient en moyenne 2 à 3 lignes (entre 1 et 6). Chaque produit n'apparaît qu'une fois par commande.

### 3.7 deliveries

La livraison de chaque commande expédiée. Une commande annulée n'a pas de livraison, et une commande « En cours » (pas encore expédiée) n'en a pas encore.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| delivery_id | texte | Identifiant de la livraison | Oui | Unique, format D000000 |
| order_id | texte | Commande livrée | Oui | Doit exister dans orders, une seule livraison par commande |
| warehouse_id | texte | Entrepôt d'expédition | Oui | Doit exister dans warehouses |
| supplier_id | texte | Fournisseur principal de la commande | Oui | Doit exister dans suppliers |
| carrier | texte | Transporteur | Oui | Valeur de la liste de référence |
| ship_date | date | Date d'expédition | Oui | Postérieure ou égale à la date de commande |
| expected_delivery_date | date | Date d'arrivée prévue | Oui | Postérieure ou égale à la date d'expédition |
| actual_delivery_date | date | Date d'arrivée réelle | Non | Postérieure ou égale à la date d'expédition. Vide si la livraison est en transit. |
| delivery_status | texte | État de la livraison | Oui | En transit ou Livrée |

Le « fournisseur principal » est le fournisseur du produit au montant le plus élevé de la commande. C'est une simplification de la première version, à confirmer (voir `data_model.md`).

### 3.8 inventory

Une photo du stock, chaque jour.

| Colonne | Type | Signification | Obligatoire | Règles |
|---|---|---|---|---|
| snapshot_date | date | Jour de la photo | Oui | Date valide, dans la période |
| product_id | texte | Produit | Oui | Doit exister dans products |
| warehouse_id | texte | Entrepôt | Oui | Doit exister dans warehouses |
| quantity_on_hand | entier | Quantité en stock à la fin de la journée | Oui | Supérieure ou égale à 0 |

Clé primaire : la combinaison des trois premières colonnes (un seul enregistrement par produit, entrepôt et jour).

## 4. Colonnes techniques ajoutées dans Bronze

Elles sont ajoutées par le chargement, pas par les sources.

| Colonne | Signification |
|---|---|
| loaded_at | Date et heure du chargement |
| batch_id | Identifiant du lot (par exemple 2026-10-01) |
| source_file | Nom du fichier d'origine |
| row_number_in_file | Position de la ligne dans le fichier |

## 5. Listes de valeurs autorisées

| Sujet | Valeurs |
|---|---|
| customer_type | Particulier, Entreprise |
| status (commandes) | En cours, Expédiée, Livrée, Annulée |
| delivery_status | En transit, Livrée |
| category | Électronique, Alimentation, Maison, Mode, Hygiène et beauté, Bureau |
| Villes (exemples) | Nador, Oujda, Casablanca, Rabat, Tanger, Fès, Marrakech, Agadir |
| Régions (exemples) | Oriental, Casablanca-Settat, Rabat-Salé-Kénitra, Tanger-Tétouan-Al Hoceïma, Fès-Meknès, Marrakech-Safi, Souss-Massa |
| Transporteurs | À définir dans `reference/carriers.csv` (4 à 5 sociétés) |

Les listes complètes se trouvent dans le dossier `data_generation/reference/`.

## 6. Les défauts à injecter

Chaque défaut a un taux (en pourcentage des lignes de la table) et un traitement attendu. Les taux sont des propositions, réglables dans `config.py`.

Les traitements possibles :
- **Corrigé** : Silver corrige et garde la ligne.
- **Dédupliqué** : Silver garde une seule ligne.
- **Remplacé** : la valeur devient « Inconnu ».
- **Rejeté** : la ligne va dans la table de quarantaine avec son motif.

### Les défauts sont injectés lot par lot

Chaque lot (le lot de base et chacun des 31 lots quotidiens) est sali séparément, avec son propre tirage au hasard, selon les taux ci-dessous. Sur un petit lot quotidien, un taux de 0,5 % peut donner zéro ou une seule ligne. Le rapport de vérité de `data/ground_truth/<lot>/` donne les nombres exacts de chaque lot.

### 6.1 customers

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Doublon exact | Même client deux fois | 2 % | Dédupliqué |
| Doublon avec casse différente | « Ali » et « ALI », même identifiant | 1 % | Dédupliqué |
| Ville avec casse différente | NADOR, nador | 15 % | Corrigé |
| Ville manquante | Vide ou NULL | 3 % | Remplacé |
| Espaces parasites | « Sara » avec espaces autour | 5 % | Corrigé |
| E-mail invalide | Sans @ | 3 % | Remplacé |
| Date d'inscription en format mixte | 01/10/2026, 2026-10-01, 1 Oct 2026 | 10 % | Corrigé |

### 6.2 suppliers

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Ville avec casse différente | RABAT, rabat | 10 % | Corrigé |
| Pays manquant | Vide | 2 % | Remplacé |
| Délai négatif | -3 jours | 1 ligne | Rejeté |
| Doublon exact | Même fournisseur deux fois | 1 ligne | Dédupliqué |

Évolution volontaire (pas un défaut) : dans le lot du 2026-10-02, deux fournisseurs ont changé de ville. Cela sert à tester l'historisation. Ces lignes ne doivent pas être corrigées, mais historisées.

### 6.3 warehouses

La table ne contient que 5 lignes, donc très peu de défauts.

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Ville avec casse différente | CASABLANCA | 1 ligne | Corrigé |
| Espaces parasites | Espaces autour du nom | 1 ligne | Corrigé |

### 6.4 products

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Doublon exact | Même produit deux fois | 1 % | Dédupliqué |
| Catégorie mal écrite | « electronique », « Electronik » | 5 % | Corrigé |
| Marque manquante | Vide | 3 % | Remplacé |
| Prix négatif | -150 | 1 % | Rejeté |
| Prix manquant | Vide | 2 % | Rejeté |
| Fournisseur inexistant | S999 | 1 % | Rejeté |

### 6.5 orders

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Doublon exact | Même commande deux fois | 1,5 % | Dédupliqué |
| Date en format mixte | 01/10/2026, 1 Oct 2026 | 15 % | Corrigé |
| Statut mal écrit | « livree », « LIVRÉE » | 3 % | Corrigé |
| Date dans le futur | 2027-03-01 | 0,5 % | Rejeté |
| Client inexistant | C99999 | 1 % | Rejeté |
| Client manquant | Vide | 0,5 % | Rejeté |
| Entrepôt inexistant | W99 | 0,5 % | Rejeté |

### 6.6 order_items

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Doublon exact | Même ligne deux fois | 1 % | Dédupliqué |
| Quantité nulle ou négative | 0, -2 | 1 % | Rejeté |
| Prix négatif ou manquant | -50, vide | 1 % | Rejeté |
| Produit inexistant | P9999 | 1 % | Rejeté |
| Commande inexistante | O999999 | 0,5 % | Rejeté |

### 6.7 deliveries

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Doublon exact | Même livraison deux fois | 1 % | Dédupliqué |
| Dates en format mixte | 01/10/2026 | 10 % | Corrigé |
| Date d'arrivée manquante alors que la livraison est marquée « Livrée » | Vide | 2 % | Signalé par un contrôle qualité, exclu du délai moyen |
| Arrivée avant l'expédition | Arrivée le 3, expédition le 5 | 1 % | Rejeté |
| Commande inexistante | O999999 | 0,5 % | Rejeté |
| Livraison d'une commande annulée | Commande Annulée avec livraison | 0,5 % | Signalé par un contrôle qualité |

Les livraisons réellement « En transit » avec une date d'arrivée vide ne sont pas un défaut : c'est un cas normal décrit dans `business_rules.md`.

### 6.8 inventory

| Défaut | Exemple | Taux | Traitement |
|---|---|---|---|
| Doublon exact | Même photo deux fois | 1 % | Dédupliqué |
| Date en format mixte | 01/10/2026 | 5 % | Corrigé |
| Quantité négative | -4 | 0,5 % | Rejeté |
| Produit ou entrepôt inconnu | P9999, W99 | 0,5 % | Rejeté |
| Jour manquant pour un produit | Trou dans la série | 0,5 % | Signalé par un contrôle qualité |

### 6.9 Règles générales sur les défauts

- Les défauts sont injectés **après** la génération des données propres, jamais pendant.
- Le taux total de lignes **rejetées** par table doit rester sous 5 % dans les lots normaux (seuil d'arrêt défini dans `business_rules.md`).
- Prévoir **un lot de test volontairement très défectueux** (par exemple 8 % de lignes à rejeter) pour vérifier que le pipeline s'arrête.
- Chaque défaut injecté est compté et écrit dans le rapport de `data/ground_truth/`.

## 7. Le rapport de vérité (`ground_truth`)

Pour chaque lot et chaque table, le rapport indique :

| Information | Exemple |
|---|---|
| Nombre de lignes propres | 1 000 |
| Nombre de lignes après injection | 1 030 |
| Défauts injectés par type | 20 doublons, 150 villes en casse différente |
| Lignes qui devraient être rejetées | 12 |
| Lignes qui devraient être corrigées | 180 |

Ce rapport sert à contrôler Silver : si tu as injecté 20 doublons, Silver doit en retrouver et écarter exactement 20.

## 8. Points à valider

- [x] Les colonnes de chaque table sont complètes pour répondre aux 10 questions métier
- [x] La période de deux ans (1er octobre 2024 au 30 septembre 2026)
- [x] Les volumes indicatifs
- [x] Les listes de catégories, villes et statuts
- [x] Le choix du « fournisseur principal » dans la table deliveries
- [x] Les taux de défauts
