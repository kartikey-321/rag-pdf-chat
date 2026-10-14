
import boto3
import os

s3_client = boto3.client("s3")

BUCKET_NAME = os.environ["S3_BUCKET_NAME"]


def upload_pdf_to_s3(file_path: str, doc_id: str):
    s3_key = f"documents/{doc_id}.pdf"

    s3_client.upload_file(
        Filename=file_path,
        Bucket=BUCKET_NAME,
        Key=s3_key,
        ExtraArgs={"ContentType": "application/pdf"}
    )

    return s3_key