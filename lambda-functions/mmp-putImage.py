import json
import os
import boto3
import base64
from io import BytesIO
import imghdr

def connect_to_s3():
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = os.environ.get('BUCKET_NAME')
    if not bucket_name:
        raise ValueError("Environment variable 'BUCKET_NAME' is not set")
    return s3, bucket_name


def validate_base64_image(image_data):
    try:
        decoded = base64.b64decode(image_data, validate=True)
        img_type = imghdr.what(None, h=decoded)

        if img_type not in ["jpeg", "png", "gif", "bmp", "webp"]:
            return None, "Unsupported image type"

        return decoded, img_type
    except Exception as e:
        return None, f"Invalid image data: {str(e)}"

def upload_to_s3(decoded_image, filename, img_type, s3, BUCKET):
    key = filename if filename.endswith(f".{img_type}") else f"{filename}.{img_type}"

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=decoded_image,
        ContentType=f"image/{img_type}",
        # ACL="public-read"  # Optional
    )
    return f"https://{BUCKET}.s3.amazonaws.com/{key}"

def add_db_record(filename, url, client_data):
    rds = boto3.client('rds-data')
    database_name = os.environ.get('DB_NAME')
    cluster_arn = os.environ.get('DB_CLUSTER_ARN')
    secret_arn = os.environ.get('DB_SECRET_ARN')

    if not all([database_name, cluster_arn, secret_arn]):
        raise ValueError("One or more RDS environment variables are not set")

    sql = """
    INSERT INTO images (filename, url, client_data)
    VALUES (:filename, :url, :client_data)
    """
    parameters = []

    response = rds.execute_statement(
        secretArn=secret_arn,
        database=database_name,
        resourceArn=cluster_arn,
        sql=sql,
        parameters=parameters
    )

    return response


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        image_data = body.get('image')
        file_name = body.get('file_name', "upload")

        decoded_image, imgType_or_error = validate_base64_image(image_data)
        if not decoded_image:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': imgType_or_error})
            }
        
        s3, BUCKET = connect_to_s3()
        url = upload_to_s3(decoded_image, file_name, imgType_or_error,s3, BUCKET)


        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Uploaded", "url": url})
        }
    

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Upload failed", "detail": str(e)})
        }
