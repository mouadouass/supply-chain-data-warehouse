FROM apache/airflow:2.10.5-python3.11

# Les tâches du pipeline tournent dans un environnement Python séparé (/home/airflow/pipeline-venv),
# pour ne pas mélanger les bibliothèques du projet avec celles d'Airflow.
USER airflow
RUN python -m venv /home/airflow/pipeline-venv \
 && /home/airflow/pipeline-venv/bin/pip install --no-cache-dir pandas numpy psycopg2-binary