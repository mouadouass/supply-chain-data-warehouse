WITH last_days AS (
    SELECT order_date, count(*) AS n FROM silver.orders GROUP BY 1 ORDER BY 1 DESC LIMIT 2
)
SELECT 'Q_CNT_001' AS rule_id, table_name, 'Aucune ligne perdue entre Bronze et Silver' AS description,
       'bloquant' AS severity,
       abs(bronze_rows - (rejected_row_level + duplicates_removed + rejected_fk + silver_rows))::bigint AS errors,
       bronze_rows || ' lignes en Bronze' AS details
FROM audit.silver_log
UNION ALL SELECT 'Q_CNT_002', table_name, 'Taux de rejet de valeur supérieur à 5 %', 'bloquant',
       CASE WHEN rejected_row_level > 0.05 * bronze_rows THEN 1 ELSE 0 END,
       round(100.0 * rejected_row_level / nullif(bronze_rows, 0), 2) || ' %'
FROM audit.silver_log
UNION ALL SELECT 'Q_CNT_003', table_name, 'Taux de rejet de valeur entre 1 % et 5 %', 'avertissement',
       CASE WHEN rejected_row_level > 0.01 * bronze_rows AND rejected_row_level <= 0.05 * bronze_rows
            THEN 1 ELSE 0 END,
       round(100.0 * rejected_row_level / nullif(bronze_rows, 0), 2) || ' %'
FROM audit.silver_log
UNION ALL SELECT 'Q_CNT_004', table_name, 'Rejets en cascade (référence vers une ligne absente ou rejetée)',
       'avertissement', rejected_fk, NULL
FROM audit.silver_log
UNION ALL SELECT 'Q_CNT_005', 'orders', 'Volume de commandes du dernier jour inférieur de 50 % à la veille',
       'avertissement',
       CASE WHEN (SELECT count(*) FROM last_days) = 2
             AND (SELECT n FROM last_days ORDER BY order_date DESC LIMIT 1)
                 < 0.5 * (SELECT n FROM last_days ORDER BY order_date ASC LIMIT 1)
            THEN 1 ELSE 0 END,
       NULL;