from airflow import DAG
from airflow.models.param import Param
from airflow.decorators import task
from airflow.utils.dates import days_ago

import os
import uuid
import boto3
import subprocess

default_args = {"owner": "openvista", "start_date": days_ago(1)}

AWS_S3_ENDPOINT = "minio:9000"
AWS_S3_PROTOCOL = os.getenv('AWS_S3_PROTOCOL', 'http') 
S3_KEY = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "openvista")

with DAG(
    dag_id="tpi",
    description="Compute Topographic Position Index (TPI) from remote COG using GDAL",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    params={
        "input_s3_url": Param(
            default="",
            type="string",
            description="S3 URL of the input TIFF (COG recommended)",
        ),
        "band": Param(1, type="number", description="Band number to read from raster"),
        "compute_edges": Param(False, type="boolean", description="Compute TPI at edges"),
    },
    tags=["raster", "tpi", "gdal", "cog"],
) as dag:

    @task()
    def run_tpi(input_s3_url: str, band: int, compute_edges: bool) -> str:
        print('Input S3 URL:', input_s3_url)
        
        path = input_s3_url.replace("s3://", "")
        bucket, key = path.split("/", 1)
        user_id, filename = key.split("/", 1)
        
        # Set environment variables for GDAL S3 access
        os.environ['AWS_S3_ENDPOINT'] = f"{AWS_S3_PROTOCOL}://{AWS_S3_ENDPOINT}"
        os.environ['AWS_ACCESS_KEY_ID'] = S3_KEY
        os.environ['AWS_SECRET_ACCESS_KEY'] = S3_SECRET
        os.environ['AWS_REGION'] = 'us-east-1'
        
        s3 = boto3.client(
            "s3",
            endpoint_url=f"{AWS_S3_PROTOCOL}://{AWS_S3_ENDPOINT}",
            aws_access_key_id=S3_KEY,
            aws_secret_access_key=S3_SECRET,
        )
        
        tmp_input = f"/tmp/input_{uuid.uuid4().hex}.tif"
        tmp_tpi = f"/tmp/tpi_{uuid.uuid4().hex}.tif"
        tmp_out = f"/tmp/tpi_cog_{uuid.uuid4().hex}.tif"
        
        print(f"Downloading {input_s3_url} to {tmp_input}")
        s3.download_file(bucket, key, tmp_input)
        
        # Compute TPI using GDAL
        print("Computing TPI with GDAL...")
        cmd = ["gdaldem", "TPI", tmp_input, tmp_tpi, "-of", "GTiff"]
        
        if int(band) != 1:
            cmd.extend(["-b", str(band)])
        if compute_edges:
            cmd.append("-compute_edges")
            
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)
        print("GDAL TPI completed successfully")
        
        # Convert to COG
        print("Converting TPI to COG...")
        cog_cmd = [
            "gdal_translate", tmp_tpi, tmp_out,
            "-of", "COG", "-co", "TILED=YES", "-co", "COMPRESS=LZW", "-co", "BLOCKSIZE=512"
        ]
        subprocess.run(cog_cmd, check=True)
        
        # Clean up temporary files
        os.remove(tmp_input)
        os.remove(tmp_tpi)

        # Upload back to S3
        out_key = f"{user_id}/outputs/tpi/{uuid.uuid4().hex}.tif"
        output_s3_url = f"s3://{S3_BUCKET_NAME}/{out_key}"
        s3.upload_file(tmp_out, S3_BUCKET_NAME, out_key)
        os.remove(tmp_out)

        return output_s3_url

    run_tpi(
        input_s3_url="{{ dag_run.conf['input_s3_url'] }}",
        band="{{ dag_run.conf.get('band', 1) }}",
        compute_edges="{{ dag_run.conf.get('compute_edges', False) }}"
    )