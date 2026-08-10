from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add scripts directory to path to import ingestion script
sys.path.insert(0, '/opt/airflow/scripts')

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'adaptive_bi_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for Adaptive BI Platform',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    # Task 1: Ingest raw CSV data into PostgreSQL
    # In airflow container, we mount the repo to /opt/airflow
    # But since we didn't mount scripts in docker-compose, we can just run bash using the python interpreter inside airflow container
    # Actually, we need to ensure pandas and sqlalchemy are available in the airflow container, or use a DockerOperator.
    # For now, let's assume we install them or run a bash script that installs them.
    
    install_reqs = BashOperator(
        task_id='install_requirements',
        bash_command='pip install pandas sqlalchemy psycopg2-binary'
    )

    run_ingestion = BashOperator(
        task_id='run_ingestion',
        bash_command='python /opt/airflow/plugins/ingest_to_postgres.py' # Assuming we mount scripts to plugins for now
    )

    # Task 2: Run dbt models (Staging)
    # We would need dbt installed in airflow or use BashOperator if dbt is installed
    run_dbt_staging = BashOperator(
        task_id='run_dbt_staging',
        bash_command='cd /opt/airflow/plugins/dbt_project && dbt run --select staging --profiles-dir .'
    )

    # Task 3: Run dbt models (Marts)
    run_dbt_marts = BashOperator(
        task_id='run_dbt_marts',
        bash_command='cd /opt/airflow/plugins/dbt_project && dbt run --select marts --profiles-dir .'
    )

    install_reqs >> run_ingestion >> run_dbt_staging >> run_dbt_marts
