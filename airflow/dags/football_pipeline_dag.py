from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta

# 1. Enterprise Default Settings
default_args = {
    'owner': 'rayen',
    'depends_on_past': False,
    'start_date': datetime(2026, 3, 26),
    'email_on_failure': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# 2. Define the DAG — TuniGoal ELT for Tunisian Ligue Professionnelle 1
with DAG(
    'tunigoal_pipeline',
    default_args=default_args,
    description='TuniGoal ELT: Football API -> Postgres Staging -> PySpark Star Schema (Tunisian Ligue Pro 1)',
    schedule_interval='@daily',
    catchup=False,
    tags=['football', 'tunisia', 'ligue_pro1', 'pyspark', 'production'],
) as dag:

    start_pipeline = EmptyOperator(task_id='start_pipeline')
    end_pipeline = EmptyOperator(task_id='end_pipeline')

    # {{ ds }} (Logical Date) makes the extract idempotent
    extract_task = BashOperator(
        task_id='extract_from_api',
        bash_command='python /opt/airflow/ingestion/extract_api.py {{ ds }}',
    )

    load_task = BashOperator(
        task_id='load_to_staging',
        bash_command='python /opt/airflow/ingestion/load_postgres.py {{ ds }}',
    )

    # spark-submit with explicit memory allocation
    transform_task = BashOperator(
        task_id='transform_star_schema',
        bash_command="""
            spark-submit \
            --master local[*] \
            --driver-memory 2G \
            --executor-memory 2G \
            --packages org.postgresql:postgresql:42.7.10 \
            /opt/airflow/ingestion/transform_raw_spark.py
        """,
    )

    start_pipeline >> extract_task >> load_task >> transform_task >> end_pipeline
