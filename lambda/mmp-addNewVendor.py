import os
import boto3
from botocore.exceptions import ClientError
import json


def get_secret(secret_name, region):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return secret

def add_db_record(vendor_data):
    rds = boto3.client('rds-data', region_name=os.environ.get('AWS_REGION'))
    database_name = os.environ.get('DB_NAME')
    cluster_arn = os.environ.get('DB_CLUSTER_ARN')
    secret_arn = os.environ.get('DB_SECRET_ARN')
    if not all([database_name, cluster_arn, secret_arn]):
        raise ValueError("One or more RDS environment variables are not set")
    
    sql = f"""
    INSERT INTO `{database_name}`.vendors (
    vendor_name,
    vendor_address_1,
    vendor_address_2,
    vendor_city,
    vendor_state,
    vendor_zip,
    vendor_ein,
    vendor_website
    ) VALUES (
    :vendor_name,
    :vendor_address_1,
    :vendor_address_2,
    :vendor_city,
    :vendor_state,
    :vendor_zip,
    :vendor_ein,
    :vendor_website
    )
    """
    
    parameters = []

    for key, value in vendor_data.items():
        if value is None:
            parameters.append({
                'name': key,
                'value': {'isNull': True}
            })
        else:
            parameters.append({
                'name': key,
                'value': {'stringValue': value}
            })

    response = rds.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=sql,
        parameters=parameters
    )

    return response


def connect_to_db():
    rds = boto3.client('rds-data', region_name=os.environ.get('AWS_REGION'))
    database_name = os.environ.get('DB_NAME')
    cluster_arn = os.environ.get('DB_CLUSTER_ARN')
    secret_arn = os.environ.get('DB_SECRET_ARN')

    response = rds.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=f"SELECT * FROM `{database_name}`.vendors WHERE vendor_name = 'Majeks Software LLC'",
        #parameters=parameters
    )
    return response


def lambda_handler(event, context):

    
    response = add_db_record(event["vendor_data"])
    #response = connect_to_db()
    # print("Database response:", response)
    # for record in response['records']:
    #     print("Record:", record[1]["stringValue"])

    return {
        'statusCode': 200,
        'body': json.dumps('MySQL connection successful')
    }