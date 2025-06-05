import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from layers.ingestion import ingest
from layers.processing import process
from layers.contentGeneration import generate_images


from airflow import DAG
from datetime import datetime

with DAG(
    dag_id="csiro_influencer_pipeline",
    start_date=datetime(2025, 5, 6),
    # schedule_interval="@weekly",
    catchup=False,
) as dag:
    ingest_task = PythonOperator(
        task_id="ingest_articles",
        python_callable=ingest,
    )
    process_task = PythonOperator(
        task_id="process_posts",
        python_callable=process,
    )
    generate_images_task = PythonOperator(
        task_id="generate_images",
        python_callable=generate_images,
    )

    ingest_task >> process_task >> generate_images_task

if __name__ == "__main__":
    ingest()
    process()
    generate_images()