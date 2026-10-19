"""Pipeline Supply Chain : Livraison -> Bronze -> Silver -> Qualité -> Gold -> Réconciliation.

Ce fichier ne contient AUCUNE logique de données : il appelle les programmes du projet
(ingestion/, transformations/, quality/) dans le bon ordre. Chaque tâche a une seule
responsabilité, donc elle peut être relancée seule.
"""
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/airflow/project"                       # le projet monté dans le conteneur
PYTHON = "/home/airflow/pipeline-venv/bin/python"      # l'environnement Python du pipeline
log = logging.getLogger(__name__)


def notify_failure(context):
    """Appelée quand une tâche échoue (après ses relances). Ici : un message clair dans les logs.
    On pourrait brancher ici un e-mail, Slack ou un webhook."""
    ti = context["task_instance"]
    log.error("ALERTE : la tâche '%s' du pipeline '%s' a échoué (exécution du %s). Logs : %s",
              ti.task_id, ti.dag_id, context["ds"], ti.log_url)


def step(task_id, module, retries=2, doc=""):
    """Une tâche = un programme du projet, lancé depuis la racine du projet."""
    return BashOperator(
        task_id=task_id,
        bash_command=f"cd {PROJECT} && {PYTHON} -m {module}",
        retries=retries,
        doc_md=doc,
    )


with DAG(
    dag_id="supply_chain_pipeline",
    description="Livraison du lot -> Bronze -> Silver -> Qualité -> Gold -> Réconciliation",
    start_date=datetime(2026, 10, 1),
    schedule="0 2 * * *",              # tous les jours à 02:00 (fuseau Africa/Casablanca)
    catchup=False,                     # ne rejoue pas les jours passés automatiquement
    max_active_runs=1,                 # jamais deux exécutions en même temps
    default_args={
        "owner": "data-engineer",
        "retries": 2,                              # 2 relances en cas d'erreur temporaire...
        "retry_delay": timedelta(minutes=5),       # ...espacées de 5 minutes
        "execution_timeout": timedelta(minutes=30),
        "on_failure_callback": notify_failure,
    },
    tags=["supply-chain", "data-warehouse"],
) as dag:

    receive_new_lot = step("receive_new_lot", "ingestion.receive_new_lot",
                           doc="La source livre le lot du jour : data/incoming/ vers data/raw/.")
    load_bronze = step("load_bronze", "ingestion.load_bronze",
                       doc="Charge les nouveaux lots de data/raw dans Bronze (un lot déjà chargé est ignoré).")
    build_silver = step("build_silver", "transformations.run_silver",
                        doc="Nettoie Bronze : doublons, formats, quarantaine des lignes invalides.")
    # Un échec de qualité ou de réconciliation n'est PAS un incident temporaire : pas de relance.
    quality_checks = step("quality_checks", "quality.run_quality", retries=0,
                          doc="76 règles. Une règle bloquante en échec arrête le pipeline avant Gold.")
    build_gold = step("build_gold", "transformations.build_gold --skip-quality",
                      doc="Construit le Star Schema (la qualité vient d'être vérifiée à l'étape précédente).")
    reconciliation = step("reconciliation", "transformations.run_reconciliation", retries=0,
                          doc="Prouve que Silver et Gold ont les mêmes chiffres.")

    receive_new_lot >> load_bronze >> build_silver >> quality_checks >> build_gold >> reconciliation