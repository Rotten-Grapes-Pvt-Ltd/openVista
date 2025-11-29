from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
import requests
import urllib.parse
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "openvista",
    "start_date": days_ago(1),
    "retries": 0,
}

def extract_cog_info(**context):
    """
    Input: s3://openvista/uuid/ndvi.tif
    Calls: http://localhost:8000/cog/info?url=<encoded>
    """
    dag_run = context['dag_run']
    conf = dag_run.conf or {}
    s3_url = conf.get("s3_url")
    # URL encode for TiTiler
    encoded = urllib.parse.quote(s3_url, safe="")

    titiler_url = f"http://host.docker.internal:8000/cog/info?url={encoded}"
    print(f"Calling TiTiler: {titiler_url}")

    resp = requests.get(titiler_url)
    resp.raise_for_status()

    info = resp.json()

    print("COG INFO RESULT:")
    print(info)

    # you can save this to DB, MinIO, or return to FastAPI
    return info

dag =  DAG(
    dag_id="cog_info_extractor",
    description="Extract COG metadata using TiTiler for a given MinIO/S3 URL",
    default_args=default_args,
    schedule_interval=None,      # triggered externally
    catchup=False,
    tags=["cog", "minio", "titiler"],
)
    

t1 = PythonOperator(
    task_id='extract_cog_info',
    python_callable=extract_cog_info,
    provide_context=True,
    dag=dag,
)
