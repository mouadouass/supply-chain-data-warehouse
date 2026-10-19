# Mesures DAX

Toutes les mesures sont dans la table `_Mesures` du fichier `supply_chain_dashboard.pbix`.
Les définitions suivent `docs/business_rules.md`.

## Ventes

Le chiffre d'affaires exclut les commandes annulées.

| Mesure | Rôle |
|---|---|
| Chiffre d'affaires | Somme des montants, hors commandes annulées |
| Nombre de commandes | Commandes distinctes non annulées |
| Quantité vendue | Unités vendues, hors annulations |
| Panier moyen | Chiffre d'affaires divisé par le nombre de commandes |
| Taux d'annulation | Commandes annulées divisées par toutes les commandes |
| CA année précédente | Même période, un an plus tôt |
| Évolution vs année précédente | Écart en % avec l'année précédente |
| Part du CA | Part d'un client dans le chiffre d'affaires affiché |

```dax
Chiffre d'affaires = CALCULATE(SUM(fact_sales[total_amount]), fact_sales[is_cancelled] = 0)
Nombre de commandes = CALCULATE(DISTINCTCOUNT(fact_sales[order_id]), fact_sales[is_cancelled] = 0)
Quantité vendue = CALCULATE(SUM(fact_sales[quantity]), fact_sales[is_cancelled] = 0)
Panier moyen = DIVIDE([Chiffre d'affaires], [Nombre de commandes])
Taux d'annulation = DIVIDE(CALCULATE(DISTINCTCOUNT(fact_sales[order_id]), fact_sales[is_cancelled] = 1), DISTINCTCOUNT(fact_sales[order_id]))
CA année précédente = CALCULATE([Chiffre d'affaires], SAMEPERIODLASTYEAR(dim_date[full_date]))
Évolution vs année précédente = DIVIDE([Chiffre d'affaires] - [CA année précédente], [CA année précédente])
Part du CA = DIVIDE([Chiffre d'affaires], CALCULATE([Chiffre d'affaires], ALLSELECTED(dim_customer)))
```

## Livraisons

La relation active avec la date est la date d'expédition. Un retard est une arrivée après la date prévue.
Le taux de retard se calcule sur les livraisons arrivées.

```dax
Nombre de livraisons = COUNTROWS(fact_delivery)
Livraisons arrivées = SUM(fact_delivery[is_delivered])
Livraisons en retard = SUM(fact_delivery[is_late])
Taux de retard = DIVIDE([Livraisons en retard], [Livraisons arrivées])
Délai moyen (jours) = AVERAGE(fact_delivery[delivery_days])
Retard moyen quand en retard (jours) = CALCULATE(AVERAGE(fact_delivery[delay_days]), fact_delivery[is_late] = 1)
```

## Stocks

Les stocks ne s'additionnent pas dans le temps : on prend le dernier jour de la période.

```dax
Dernière date de stock = CALCULATE(MAX(dim_date[full_date]), fact_inventory)
Stock disponible = VAR d = [Dernière date de stock] RETURN CALCULATE(SUM(fact_inventory[quantity_on_hand]), dim_date[full_date] = d)
Produits en rupture = VAR d = [Dernière date de stock] RETURN CALCULATE(SUM(fact_inventory[is_out_of_stock]), dim_date[full_date] = d)
Jours de rupture = SUM(fact_inventory[is_out_of_stock])
Taux de rupture = DIVIDE([Jours de rupture], COUNTROWS(fact_inventory))
```

## Modèle

15 relations plusieurs-à-un, de la table de faits vers la dimension. Pour `fact_delivery`, la relation
active avec `dim_date` est `ship_date_key` ; les dates de commande, prévue et réelle sont inactives.
`dim_date` est marquée comme table de dates (sans la ligne « Inconnu »).