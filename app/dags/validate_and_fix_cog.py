from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from airflow.models.param import Param

import os
import requests
import boto3
import subprocess
from urllib.parse import quote_plus

default_args = {
    "owner": "openvista",
    "start_date": days_ago(1),
    "retries": 0,
}

TITILER_ENDPOINT = os.getenv("TITILER_ENDPOINT")
AWS_S3_ENDPOINT = "minio:9000" # os.getenv("AWS_S3_ENDPOINT", "minio:9000")  # Default to Docker service name
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_PROTOCOL = os.getenv('AWS_S3_PROTOCOL', 'http')  # Default to http for MinIO
with DAG(
    dag_id="validate_and_fix_cog",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    params={
        "input_s3_url": Param("", type="string", description="S3 URL of TIFF")
    },
    tags=["cog", "validation", "minio"],
) as dag:

    @task()
    def validate_cog(input_s3_url: str) -> dict:
        """
        Call TiTiler /cog/validate to check COG status.
        """
        encoded = quote_plus(input_s3_url)
        url = f"{TITILER_ENDPOINT}/cog/validate?url={encoded}"

        print("Calling:", url)
        response = requests.get(url)
        response.raise_for_status()

        result = response.json()
        print("Validation Result:", result)
        return {
            "is_cog": result["COG"],
            "url": input_s3_url
        }

    @task()
    def convert_to_cog_if_needed(data: dict) -> str:
        """
        If TIFF is NOT a COG, convert it using GDAL.
        """
        is_cog = data["is_cog"]
        input_s3_url = data["url"]

        if is_cog:
            print("File is already a valid COG. Nothing to do.")
            return input_s3_url

        print("File is NOT a COG. Converting...")

        # Extract bucket + key
        path = input_s3_url.replace("s3://", "")
        bucket, key = path.split("/", 1)

        from botocore.config import Config
        
        config = Config(
            read_timeout=60,
            connect_timeout=60,
            retries={'max_attempts': 3},
            signature_version='s3v4'
        )
        
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=f"{AWS_S3_PROTOCOL}://{AWS_S3_ENDPOINT}",
            config=config,
            use_ssl=False if AWS_S3_PROTOCOL == 'http' else True
        )
        
        print(f"S3 endpoint: {AWS_S3_PROTOCOL}://{AWS_S3_ENDPOINT}")
        print(f"Bucket: {bucket}, Key: {key}")

        tmp_in = "/tmp/input.tif"
        tmp_out = "/tmp/output.tif"

        # DOWNLOAD TIFF
        print(f"Downloading {bucket}/{key} → {tmp_in}")
        try:
            s3.download_file(bucket, key, tmp_in)
            print(f"Download completed. File size: {os.path.getsize(tmp_in)} bytes")
        except Exception as e:
            print(f"Download failed: {str(e)}")
            raise

        # CONVERT TO COG with proper parameters
        cmd = [
            "gdal_translate",
            tmp_in,
            tmp_out,
            "-of", "COG",
            "-co", "TILED=YES",
            "-co", "COPY_SRC_OVERVIEWS=YES",
            "-co", "COMPRESS=LZW",
            "-co", "BLOCKSIZE=512"
        ]

        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)
        
        # Verify COG creation
        verify_cmd = ["gdalinfo", "-checksum", tmp_out]
        print("Verifying COG:", " ".join(verify_cmd))
        result = subprocess.run(verify_cmd, capture_output=True, text=True)
        print("GDAL Info Output:", result.stdout)
        
        print(f"Output file size: {os.path.getsize(tmp_out)} bytes")

        # UPLOAD BACK (overwrite original!)
        print(f"Uploading COG back to {bucket}/{key}")
        s3.upload_file(tmp_out, bucket, key)
        print("Upload completed successfully")

        return input_s3_url

    # Pipeline
    validate_result = validate_cog(
        input_s3_url="{{ dag_run.conf['input_s3_url'] }}"
    )
    
    # Conditionally convert only if not a COG
    convert_result = convert_to_cog_if_needed(validate_result)
