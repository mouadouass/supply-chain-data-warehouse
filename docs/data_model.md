# Modèle de données

Ce document explique **comment est construit l'entrepôt et pourquoi** : les relations entre les tables sources, le grain des tables de faits, les clés, les dimensions, l'historisation et les choix de conception.

Le détail des colonnes sources est dans `data_dictionary.md`. Les définitions métier sont dans `business_rules.md`.

## 1. Les relations entre les tables sources

| Table | Référence (clé étrangère) |
|---|---|
| products | supplier_id vers suppliers |
| orders | customer_id vers customers, warehouse_id vers warehouses |
| order_items | order_id vers orders, product_id vers products |
| deliveries | order_id vers orders, warehouse_id vers warehouses, supplier_id vers suppliers |
| inventory | product_id vers products, warehouse_id vers warehouses |

Lecture simple : un client passe une commande, qui part d'un entrepôt, contient des produits, chaque produit vient d'un fournisseur, et la commande est livrée.

## 2. Les couches

| Couche | Schéma PostgreSQL | Contenu |
|---|---|---|
| Bronze | `bronze` | Copie brute des sources, tout en texte |
| Silver | `silver` | Données nettoyées et typées, tables de passage, quarantaine |
| Gold | `gold` | Le Star Schema : dimensions, faits et vues |
| Audit | `audit` | Journal des lots, des exécutions Silver, des contrôles qualité et de la réconciliation |

La couche Gold et le Data Warehouse sont la même chose.

## 3. Le Star Schema

```text
                        dim_date
                           │
 dim_customer ──── fact_sales ──── dim_product ──── (fournisseur du produit)
                           │                              │
                     dim_warehouse                   dim_supplier

 dim_customer ─┐
 dim_supplier ─┼─── fact_delivery ──── dim_date (4 rôles)
 dim_warehouse ┘

 dim_product ──── fact_inventory ──── dim_warehouse
                        │
                     dim_date
```

Les dimensions sont **partagées** : on peut comparer ventes, livraisons et stocks pour un même entrepôt, un même produit ou une même date.

## 4. Le grain de chaque table de faits

| Table de faits | Une ligne représente | Nature |
|---|---|---|
| `fact_sales` | Un produit vendu dans une commande | Transactionnelle |
| `fact_delivery` | Une livraison (une par commande expédiée et non annulée) | Cycle de vie, avec plusieurs dates |
| `fact_inventory` | Un produit, dans un entrepôt, pour un jour donné | Photo périodique |

- Une commande de 3 produits donne **3 lignes** dans `fact_sales` mais **1 ligne** dans `fact_delivery` : pour compter les commandes, on compte les `order_id` **distincts**.
- Les stocks ne s'additionnent pas dans le temps : on prend le dernier jour ou la moyenne.

## 5. Les dimensions et leurs colonnes

| Dimension | Colonnes | Historisée (SCD Type 2) sur |
|---|---|---|
| `dim_date` | date_key, full_date, year, quarter, month, month_name, year_month, week_of_year, day_of_month, day_of_week, day_name, is_weekend, is_holiday, holiday_name | non (une ligne par jour, du 2023-01-01 au 2028-12-31) |
| `dim_customer` | customer_key, customer_id, customer_name, customer_type, email, city, region, registration_date, start_date, end_date, is_current | la **région** |
| `dim_product` | product_key, product_id, product_name, category, brand, unit_price (prix catalogue actuel), supplier_id, created_date, start_date, end_date, is_current | la **catégorie** |
| `dim_supplier` | supplier_key, supplier_id, supplier_name, city, country, standard_lead_time_days, start_date, end_date, is_current | la **ville** |
| `dim_warehouse` | warehouse_key, warehouse_id, warehouse_name, city, region, capacity_units | non |

La clé de `dim_date` est un entier `AAAAMMJJ` (le 1er octobre 2026 donne 20261001). Les jours fériés sont ceux à date fixe ; les fêtes religieuses (dates lunaires) ne sont pas incluses.

## 6. Les tables de faits et leurs colonnes

| Fait | Colonnes |
|---|---|
| `fact_sales` | sales_key, order_item_id, order_id, customer_key, product_key, supplier_key, warehouse_key, date_key, order_status, is_cancelled, quantity, unit_price, total_amount |
| `fact_delivery` | delivery_key, delivery_id, order_id, customer_key, supplier_key, warehouse_key, order_date_key, ship_date_key, expected_date_key, actual_date_key, carrier, delivery_status, delivery_days, delay_days, is_delivered, is_late, is_missing_arrival |
| `fact_inventory` | date_key, product_key, warehouse_key, quantity_on_hand, is_out_of_stock, is_low_stock |

Les commandes annulées sont **conservées** dans `fact_sales` avec `is_cancelled = 1` ; la mesure du chiffre d'affaires les exclut. Cela permet de calculer le taux d'annulation.

## 7. Les clés

| Clé | Exemple | Origine | Pourquoi |
|---|---|---|---|
| Identifiant source (`_id`) | S002 | Le système d'origine | Retrouver l'entité d'origine |
| Clé de substitution (`_key`) | 3 | Créée par l'entrepôt | Distinguer les versions d'une même entité |

Un fournisseur qui change de ville a **un seul** `supplier_id` mais **deux** `supplier_key`.

`order_id` et `order_item_id` sont conservés dans les faits sans dimension propre : ce sont des **dimensions dégénérées**. Elles permettent de compter les commandes distinctes et de relier ventes et livraisons.

## 8. Les quatre rôles de la date dans fact_delivery

Une livraison porte plusieurs dates. On utilise la **même dimension `dim_date`** avec un rôle différent à chaque fois.

| Rôle | Colonne |
|---|---|
| Date de commande | order_date_key |
| Date d'expédition | ship_date_key |
| Date prévue | expected_date_key |
| Date réelle | actual_date_key (vaut -1 si la livraison n'est pas arrivée) |

Dans Power BI, une seule relation est active (la date d'expédition), les trois autres sont inactives.

## 9. La ligne « Inconnu » (clé -1)

Chaque dimension contient une ligne de clé **-1** : une référence manquante ne fait perdre aucune vente. Les lignes **rejetées** en Silver (client inexistant, produit inexistant) n'arrivent pas dans Gold : elles restent en quarantaine. Après construction, aucune ligne de fait ne pointe vers « Inconnu ».

## 10. L'historisation (SCD Type 2)

| Dimension | Attribut suivi |
|---|---|
| dim_supplier | Ville |
| dim_product | Catégorie |
| dim_customer | Région |

### Principe

1. Silver garde une ligne par **version** des tables de référence (une nouvelle ligne seulement si une valeur change d'un lot à l'autre).
2. Gold repère les changements de l'attribut suivi, numérote les versions, et ne garde qu'une ligne par version.
3. Les autres attributs (nom, e-mail...) prennent toujours la valeur la plus récente.

### Les dates de validité

- La **première version** d'une entité commence le `1900-01-01`.
- Une **nouvelle version** commence au jour des données du lot où elle apparaît (le lot du 2026-10-02 porte les données du 2026-10-01).
- La fin d'une version est la **veille** du début de la suivante.
- La version actuelle finit le `9999-12-31`, ce qui permet de joindre un fait à sa dimension avec un simple `BETWEEN` sur la date.

### Exemple

| supplier_key | ville | start_date | end_date | is_current |
|---|---|---|---|---|
| 2 | Marrakech | 1900-01-01 | 2026-09-30 | non |
| 3 | Rabat | 2026-10-01 | 9999-12-31 | oui |

### Utilisation dans les faits

Chaque ligne de fait prend la version de la dimension **valable à la date de l'événement** : les ventes d'avant le 1er octobre restent rattachées à Marrakech.

### Cas de test

Deux fournisseurs (S002 et S009) changent de ville dans le **dernier lot quotidien** (2026-10-02). Ils n'ont donc leurs deux versions qu'une fois ce lot livré et traité.

## 11. Les vues pour Power BI

| Vue | Contenu |
|---|---|
| `vw_sales_summary` | Chiffre d'affaires, quantités et commandes par mois, catégorie, région du client et fournisseur (commandes annulées exclues) |
| `vw_delivery_performance` | Livraisons, retards, taux de retard, délai moyen par mois d'expédition, fournisseur et entrepôt |
| `vw_inventory_status` | État actuel de chaque produit par entrepôt : quantité, ventes des 30 derniers jours, jours de rupture, statut (Rupture, Stock bas, Dormant, Normal) |

## 12. Comment Gold est construit

- Gold est **reconstruit en entier** à chaque lancement : dimensions d'abord, puis ligne « Inconnu », puis faits, puis vues.
- Les clés de substitution sont recalculées à chaque reconstruction ; les faits sont reconstruits avec elles, donc les relations restent cohérentes.
- Gold refuse de démarrer si une règle qualité **bloquante** échoue.
- La réconciliation compare ensuite Silver et Gold (lignes, chiffre d'affaires par mois, doublons, versions qui se chevauchent).

## 13. Les choix de conception

| Sujet | Choix retenu | Alternative écartée |
|---|---|---|
| Fournisseur d'une livraison | Fournisseur du produit au montant le plus élevé de la commande | Une livraison par fournisseur impliqué |
| Transporteur | Colonne texte dans `fact_delivery` | Dimension `dim_carrier` |
| Stock | Une photo par jour, produit et entrepôt | Photo hebdomadaire |
| Prix | Prix payé dans `fact_sales` ; prix catalogue actuel dans `dim_product` | Historiser le prix du catalogue |
| Dimension date | Générée une fois, de 2023 à 2028 | Générée à partir des faits |
| Livraisons de commandes annulées | Exclues de `fact_delivery` (anomalie signalée par la qualité) | Les garder avec un indicateur |
| Version actuelle d'une dimension | `end_date = 9999-12-31` | `end_date` vide |
| Reconstruction | Complète à chaque lancement | Chargement incrémental |

## 14. Journal des décisions

| Étape | Décision | Raison |
|---|---|---|
| 2 | Le grain de `fact_sales` est la ligne de commande | Permet l'analyse par produit et par catégorie |
| 2 | Une table `order_items` en plus de `orders` | Nécessaire pour ce grain |
| 6 | Silver garde les versions des tables de référence | Rend possible le SCD Type 2 |
| 8 | Seul l'attribut suivi déclenche une nouvelle version | Les autres changements ne doivent pas multiplier les lignes |
| 8 | `end_date = 9999-12-31` | Simplifie les jointures par date |
| 8 | Ligne « Inconnu » dans chaque dimension | Aucune vente perdue |
| 9 | Contrôles de réconciliation après Gold | Détecter les jointures qui dupliquent des lignes |
| 11 | KPIs en mesures DAX, stocks sur le dernier jour | Les mesures réagissent aux filtres ; un stock ne s'additionne pas |
