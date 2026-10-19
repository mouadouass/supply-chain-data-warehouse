# Questions métier

Ce document liste les questions auxquelles le dashboard doit répondre. Chaque question correspond à une décision possible. Si un graphique ne sert à aucune décision, il n'a pas sa place dans le dashboard.

## Les 10 questions prioritaires

### Direction générale

**Q1. Quel est le chiffre d'affaires total, et comment évolue-t-il mois par mois par rapport à la même période de l'année précédente ?**
- Décision possible : ajuster les objectifs et le budget, repérer la saisonnalité.
- Source : ventes, dimension date.

**Q2. Quelles régions et quelles catégories de produits génèrent le plus de chiffre d'affaires ?**
- Décision possible : choisir où investir, quelle région développer.
- Source : ventes, dimensions client, produit et date.

### Responsable commercial

**Q3. Qui sont les 10 meilleurs clients, et quelle part du chiffre d'affaires représentent-ils ?**
- Décision possible : fidéliser les clients clés, mesurer la dépendance à quelques clients.
- Source : ventes, dimension client.

**Q4. Quels produits et quelles catégories progressent ou reculent d'un trimestre à l'autre ?**
- Décision possible : mettre en avant, remplacer ou arrêter un produit.
- Source : ventes, dimensions produit et date.

### Responsable logistique

**Q5. Quel est le délai moyen de livraison et le taux de retard, mois par mois ?**
- Décision possible : détecter une dégradation du service avant que les clients se plaignent.
- Source : livraisons, dimension date.

**Q6. Quel entrepôt a le délai le plus long et le taux de retard le plus élevé ?**
- Décision possible : réorganiser un entrepôt, rééquilibrer les expéditions.
- Source : livraisons, dimension entrepôt.

### Responsable achats

**Q7. Quels fournisseurs sont à l'origine du plus grand nombre de retards, et quel est leur délai moyen ?**
- Décision possible : renégocier, mettre sous surveillance ou changer de fournisseur.
- Source : livraisons, dimension fournisseur.

**Q8. Quelle part du chiffre d'affaires dépend de chaque fournisseur ?**
- Décision possible : réduire la dépendance à un fournisseur unique.
- Source : ventes, dimensions produit et fournisseur.

### Responsable stock

**Q9. Quels produits sont en rupture, dans quel entrepôt, et pendant combien de jours par mois ?**
- Décision possible : relever le stock de sécurité, avancer les réapprovisionnements.
- Source : stocks, dimensions produit, entrepôt et date.

**Q10. Quel est le stock par entrepôt, et quels produits dorment sans être vendus ?**
- Décision possible : déstocker, arrêter de réapprovisionner, transférer entre entrepôts.
- Source : stocks et ventes, dimensions produit et entrepôt.

## Tableau récapitulatif

| N° | Pour qui | Thème | KPI associé |
|---|---|---|---|
| Q1 | Direction | Ventes | Chiffre d'affaires, évolution |
| Q2 | Direction | Ventes | Chiffre d'affaires par région et catégorie |
| Q3 | Commercial | Clients | Top 10 clients, part du chiffre d'affaires |
| Q4 | Commercial | Produits | Évolution par produit et catégorie |
| Q5 | Logistique | Livraisons | Délai moyen, taux de retard |
| Q6 | Logistique | Livraisons | Retard par entrepôt |
| Q7 | Achats | Fournisseurs | Retard par fournisseur |
| Q8 | Achats | Fournisseurs | Part du chiffre d'affaires par fournisseur |
| Q9 | Stock | Stocks | Produits en rupture, jours de rupture |
| Q10 | Stock | Stocks | Stock par entrepôt, stock dormant |

## Les trois pages du dashboard

| Page | Questions couvertes |
|---|---|
| Ventes | Q1, Q2, Q3, Q4, Q8 |
| Livraisons | Q5, Q6, Q7 |
| Stocks | Q9, Q10 |

## Question bonus pour l'historisation

**Les ventes d'un fournisseur qui a changé de ville sont-elles rattachées à la bonne ville pour chaque période ?**
Cette question n'est pas pour un manager, mais elle démontre l'utilité de l'historisation (SCD Type 2). Elle servira de test : les ventes de 2025 doivent rester rattachées à l'ancienne ville.

## Hors périmètre de la première version

- les retours clients et les remboursements ;
- les remises et les taxes détaillées ;
- les prévisions de ventes et de stocks ;
- les coûts de transport et la marge.

Ces sujets pourront être ajoutés plus tard, une fois le socle terminé.
