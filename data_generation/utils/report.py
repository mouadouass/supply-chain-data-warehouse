"""Le rapport de vérité : combien de défauts de chaque type ont été injectés.

Silver devra retrouver exactement ces chiffres.
"""
import pandas as pd

CORRIGE = "Corrigé"
DEDUP = "Dédupliqué"
REMPLACE = "Remplacé"
REJETE = "Rejeté"
SIGNALE = "Signalé"
HISTORISE = "Historisé (SCD2)"


class DefectReport:
    def __init__(self, lot):
        self.lot = lot
        self._defects = []
        self._counts = {}

    def add(self, table, defect, rows, treatment):
        self._defects.append({"table": table, "defect": defect,
                              "rows_affected": int(rows), "expected_treatment": treatment})

    def record_counts(self, table, clean_rows, dirty_rows):
        self._counts[table] = (int(clean_rows), int(dirty_rows))

    def defects(self):
        return pd.DataFrame(self._defects, columns=["table", "defect", "rows_affected",
                                                    "expected_treatment"])

    def summary(self):
        d = self.defects()
        rows = []
        for table, (clean, dirty) in self._counts.items():
            sub = d[d["table"] == table]

            def total(treatment):
                return int(sub.loc[sub["expected_treatment"] == treatment, "rows_affected"].sum())

            rejected = total(REJETE)
            rows.append({
                "table": table, "clean_rows": clean, "dirty_rows": dirty,
                "expected_duplicates_removed": total(DEDUP),
                "expected_rejected": rejected,
                "reject_rate_pct": round(100 * rejected / clean, 2) if clean else 0,
                "expected_corrected": total(CORRIGE),
                "expected_replaced": total(REMPLACE),
                "expected_flagged": total(SIGNALE),
            })
        return pd.DataFrame(rows)

    def write(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        self.defects().to_csv(folder / "defects_report.csv", index=False, encoding="utf-8")
        self.summary().to_csv(folder / "tables_summary.csv", index=False, encoding="utf-8")

    def print_summary(self):
        print(f"\n--- Lot {self.lot} : résumé des défauts injectés ---")
        print(self.summary().to_string(index=False))
