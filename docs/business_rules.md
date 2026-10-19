# Règles métier et définitions

Ce document fixe la définition exacte de chaque notion utilisée dans le projet. Chaque définition ci-dessous est une **proposition de départ**. Tu peux la changer, mais une fois choisie, elle doit être appliquée partout de la même façon (génération, nettoyage, contrôles, Power BI).

Pour chaque règle, la colonne « Décision » est à confirmer ou à modifier.

## 1. Les définitions principales

### 1.1 Livraison en retard

| Point | Proposition |
|---|---|
| Définition | Une livraison est en retard si la date d'arrivée réelle est **postérieure** à la date d'arrivée prévue. |
| Livraison à l'heure | Arrivée le jour prévu ou avant. |
| Retard en jours | Date d'arrivée réelle moins date prévue (zéro si à l'heure). |
| Taux de retard | Nombre de livraisons en retard divisé par le nombre de livraisons arrivées. |
| Décision | À confirmer |

### 1.2 Délai de livraison

| Point | Proposition |
|---|---|
| Définition | Nombre de jours calendaires entre la date d'expédition et la date d'arrivée réelle. |
| Délai moyen | Moyenne sur les livraisons arrivées uniquement. |
| Décision | À confirmer |

### 1.3 Rupture de stock

| Point | Proposition |
|---|---|
| Définition | Un produit est en rupture dans un entrepôt quand sa quantité en stock est égale à zéro à la fin de la journée. |
| Stock bas (alerte) | Quantité inférieure ou égale à un seuil par défaut de 10 unités. |
| Jours de rupture | Nombre de jours dans la période où le produit est en rupture. |
| Décision | À confirmer, et à ajuster selon les volumes générés |

### 1.4 Chiffre d'affaires

| Point | Proposition |
|---|---|
| Définition | Somme, pour chaque ligne de commande, de la quantité multipliée par le prix unitaire. |
| Taxes | Hors taxes. |
| Remises | Non gérées dans la première version : le prix unitaire est le prix payé. |
| Frais de livraison | Exclus. |
| Commandes annulées | Exclues. |
| Devise | Dirham marocain (MAD) partout. |
| Décision | À confirmer |

### 1.5 Commande annulée

| Point | Proposition |
|---|---|
| Statuts possibles | En cours, expédiée, livrée, annulée. |
| Traitement | Exclue du chiffre d'affaires, du nombre de commandes et des livraisons. |
| Conservation | Gardée dans Silver et Gold avec son statut, pour pouvoir calculer un taux d'annulation. |
| Livraison associée | Une commande annulée n'a pas de livraison. Si elle en a une, c'est une anomalie détectée par les contrôles. |
| Décision | À confirmer |

### 1.6 Livraison sans date d'arrivée

Deux cas différents, à ne pas mélanger :

| Cas | Traitement |
|---|---|
| La date prévue n'est pas encore dépassée | Statut « en transit ». Exclue du délai moyen et du taux de retard. |
| La date prévue est dépassée sans arrivée | Statut « non livrée en retard ». Exclue du délai moyen, mais comptée dans un indicateur séparé « livraisons non arrivées en retard » et signalée par un contrôle qualité. |
| Décision | À confirmer |

## 2. Les indicateurs (KPIs) en mots

| Indicateur | Définition |
|---|---|
| Chiffre d'affaires total | Somme des montants des lignes de commande non annulées. |
| Nombre de commandes | Nombre de commandes distinctes non annulées. |
| Nombre de livraisons | Nombre de livraisons arrivées. |
| Délai moyen | Moyenne des délais de livraison (voir 1.2). |
| Taux de retard | Livraisons en retard divisées par livraisons arrivées. |
| Stock disponible | Dernière quantité connue par produit et par entrepôt. |
| Taux d'annulation | Commandes annulées divisées par le total des commandes. |
| Panier moyen | Chiffre d'affaires divisé par le nombre de commandes. |

## 3. Les règles de qualité des données

### 3.1 Valeurs invalides

| Cas | Traitement |
|---|---|
| Quantité nulle ou négative | Ligne rejetée vers la quarantaine, avec le motif. |
| Prix négatif | Ligne rejetée vers la quarantaine. |
| Prix manquant | Ligne rejetée vers la quarantaine. |
| Date impossible | Ligne rejetée vers la quarantaine. |
| Date de livraison antérieure à la date de commande | Ligne rejetée vers la quarantaine. |
| Date dans le futur | Ligne rejetée vers la quarantaine. |

### 3.2 Références manquantes

| Cas | Traitement |
|---|---|
| Commande sans client ou avec un client inexistant | Rejetée en Silver. |
| Ligne de commande avec un produit inexistant | Rejetée en Silver. |
| Valeur facultative manquante (ville d'un client, par exemple) | Remplacée par « Inconnu » et conservée. |
| Dimension manquante dans Gold | La ligne pointe vers le membre « Inconnu » (clé -1), pour ne perdre aucune vente. |

### 3.3 Doublons

| Cas | Traitement |
|---|---|
| Même identifiant présent plusieurs fois | On garde la ligne la plus récente (selon la date de chargement), les autres sont écartées. |

### 3.4 Seuils d'arrêt du pipeline

| Situation | Action |
|---|---|
| Identifiant vide ou doublon d'une clé après nettoyage | Le pipeline s'arrête. |
| Taux de lignes rejetées supérieur à 5 % pour une table | Le pipeline s'arrête. |
| Taux de rejet entre 1 % et 5 % | Avertissement, le pipeline continue. |
| Volume du jour inférieur de plus de 50 % à la veille | Avertissement. |

Les seuils sont des propositions à ajuster une fois les données générées.

## 4. Les règles de standardisation

| Sujet | Règle |
|---|---|
| Villes | Première lettre en majuscule, sans espaces parasites (NADOR, nador, Nador deviennent Nador). |
| Dates | Format unique année-mois-jour (2026-10-01). |
| Textes | Espaces inutiles supprimés, casse homogène. |
| Montants | Deux décimales, en dirhams. |
| Identifiants | Format fixe par table, sans espaces. |

## 5. L'historisation (SCD Type 2)

| Dimension | Attribut suivi | Historisé ? |
|---|---|---|
| Fournisseur | Ville | Oui |
| Produit | Catégorie | Oui |
| Client | Région | Oui |
| Entrepôt | Ville | Non (ne change pas) |

Règle générale : une **vraie évolution** (un fournisseur déménage) crée une nouvelle version. Une **correction d'erreur** (faute de frappe) écrase l'ancienne valeur sans créer de version.

## 6. Le grain des tables de faits

| Table | Une ligne représente |
|---|---|
| Ventes | Un produit vendu dans une commande |
| Livraisons | Une livraison |
| Stocks | Un produit, dans un entrepôt, pour un jour donné |

## 7. Le temps

| Sujet | Règle |
|---|---|
| Période couverte | Du 1er octobre 2024 au 1er octobre 2026 (2 ans) |
| Unité de temps | Jour calendaire |
| Fréquence de chargement | Quotidienne : un lot livré et traité chaque nuit à 02h00 |
| Photo de stock | Une par jour et par produit et par entrepôt |

## 8. Les décisions à valider avant de passer à la suite

- [x] Définition du retard (1.1)
- [x] Définition du délai (1.2)
- [x] Définition de la rupture et seuil de stock bas (1.3)
- [x] Définition du chiffre d'affaires (1.4)
- [x] Traitement des commandes annulées (1.5)
- [x] Traitement des livraisons sans date d'arrivée (1.6)
- [x] Règles de rejet et seuils d'arrêt (3)
- [x] Attributs historisés (5)
- [x] Période de deux ans confirmée (7)

## 9. Journal des changements

| Date | Règle modifiée | Raison |
|---|---|---|
| Étape 6 | Le taux de rejet qui arrête le pipeline ne compte que les rejets de valeur | Les rejets en cascade gonfleraient le taux et bloqueraient à tort |
| Étape 8 | Les livraisons de commandes annulées sont exclues de Gold | Anomalie signalée par la qualité (Q_DATE_007) |
| Étape 8 | Une commande « En cours » n'a pas encore de livraison | Elle n'est pas expédiée |
| Étape 8 | Le stock bas (10 unités ou moins) comprend la rupture | Un seul seuil, simple à expliquer |
| Étape 10 | Un lot de données est livré chaque nuit | La source simulée se comporte comme une vraie source |

Chaque fois qu'une définition change, on la note ici avec la raison. Cela montre ta réflexion et évite les incohérences entre les documents.
