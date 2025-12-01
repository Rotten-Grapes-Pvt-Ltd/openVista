from airflow import DAG
from airflow.models.param import Param
from airflow.decorators import task
from airflow.utils.dates import days_ago

import os
import uuid
import boto3
import subprocess
import tempfile


default_args = {"owner": "openvista", "start_date": days_ago(1)}

AWS_S3_ENDPOINT = "minio:9000"
AWS_S3_PROTOCOL = os.getenv('AWS_S3_PROTOCOL', 'http') 
S3_KEY = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "openvista")

with DAG(
    dag_id="hillshade",
    description="Compute hillshade from remote COG using GDAL",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,

    # ⭐ Here are your params
    params={
        "input_s3_url": Param(
            default="",
            type="string",
            description="S3 URL of the input TIFF (COG recommended)",
        ),
        "band": Param(1, type="number", description="Band number to read from raster"),
        "z_factor": Param(1.0, type="number", description="Vertical exaggeration"),
        "scale": Param(1.0, type="number", description="Horizontal scale"),
        "azimuth": Param(315.0, type="number", description="Azimuth of light source"),
        "altitude": Param(45.0, type="number", description="Altitude of light source"),
    },

    tags=["raster", "hillshade", "gdal", "cog"],
) as dag:

    @task()
    def run_hillshade(input_s3_url:str,
                      band: int,
                      z_factor: float,
                      scale: float,
                      azimuth: float,
                      altitude: float) -> str:
        """
        params is auto-filled from dag_run.conf or UI.
        """
       
        print('my s3 url is', input_s3_url)
        # ----- Parse bucket and key -----
        path = input_s3_url.replace("s3://", "")
        print('my path url is', path)

        bucket, key = path.split("/", 1)
        user_id, filename = key.split("/", 1)
        # ----- Open raster lazily -----
        vsis3_url = f"/vsis3/{path}"
        print("Reading remote COG:", vsis3_url)
        # Set environment variables for GDAL S3 access
        os.environ['AWS_S3_ENDPOINT'] = f"{AWS_S3_PROTOCOL}://{AWS_S3_ENDPOINT}"
        os.environ['AWS_ACCESS_KEY_ID'] = S3_KEY
        os.environ['AWS_SECRET_ACCESS_KEY'] = S3_SECRET
        os.environ['AWS_REGION'] = 'us-east-1'
        
        # ---------------- Download file temporarily ----------------
        s3 = boto3.client(
            "s3",
            endpoint_url=f"{AWS_S3_PROTOCOL}://{AWS_S3_ENDPOINT}",
            aws_access_key_id=S3_KEY,
            aws_secret_access_key=S3_SECRET,
        )
        
        tmp_input = f"/tmp/input_{uuid.uuid4().hex}.tif"
        tmp_hillshade = f"/tmp/hillshade_{uuid.uuid4().hex}.tif"
        tmp_out = f"/tmp/hillshade_cog_{uuid.uuid4().hex}.tif"
        
        print(f"Downloading {input_s3_url} to {tmp_input}")
        s3.download_file(bucket, key, tmp_input)
        
        # ---------------- Compute hillshade using GDAL ----------------
        print("Computing hillshade with GDAL...")
        cmd = [
            "gdaldem",
            "hillshade",
            tmp_input,
            tmp_hillshade,
            "-z", str(z_factor),
            "-s", str(scale),
            "-az", str(azimuth),
            "-alt", str(altitude),
            "-of", "GTiff"
        ]
        
        if int(band) != 1:
            cmd.extend(["-b", str(band)])
            
        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("GDAL hillshade completed successfully")
        
        # ---------------- Convert to COG ----------------
        print("Converting hillshade to COG...")
        cog_cmd = [
            "gdal_translate",
            tmp_hillshade,
            tmp_out,
            "-of", "COG",
            "-co", "TILED=YES",
            "-co", "COMPRESS=LZW",
            "-co", "BLOCKSIZE=512"
        ]
        
        print("Running:", " ".join(cog_cmd))
        subprocess.run(cog_cmd, check=True)
        print("COG conversion completed successfully")
        
        # Clean up temporary files
        os.remove(tmp_input)
        os.remove(tmp_hillshade)

        # ---------------- Upload back to S3 ----------------
        out_key = f"{user_id}/outputs/hillshade/{uuid.uuid4().hex}.tif"
        output_s3_url = f"s3://{S3_BUCKET_NAME}/{out_key}"

        print(f"Uploading {tmp_out} → {output_s3_url}")
        s3.upload_file(tmp_out, S3_BUCKET_NAME, out_key)
        
        # Clean up output file
        os.remove(tmp_out)

        return output_s3_url

    run_hillshade(input_s3_url="{{ dag_run.conf['input_s3_url'] }}",
                  band="{{ dag_run.conf.get('band', 1) }}",
                  z_factor="{{ dag_run.conf.get('z_factor', 1.0) }}",
                  scale="{{ dag_run.conf.get('scale', 1.0) }}",
                  azimuth="{{ dag_run.conf.get('azimuth', 315.0) }}",
                  altitude="{{ dag_run.conf.get('altitude', 45.0) }}")
