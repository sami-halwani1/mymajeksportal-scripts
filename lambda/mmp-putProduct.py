import os
import boto3
from botocore.exceptions import ClientError
import json


def getVendorDetails(event):
    rds = boto3.client('rds-data', region_name=os.environ.get('AWS_REGION'))
    database_name = os.environ.get('DB_NAME')
    cluster_arn = os.environ.get('DB_CLUSTER_ARN')
    secret_arn = os.environ.get('DB_SECRET_ARN')
    if not all([database_name, cluster_arn, secret_arn]):
        raise ValueError("One or more RDS environment variables are not set")
    
    sql = f"""
    SELECT * FROM `{database_name}`.vendors WHERE id = :id
    """
    parameters = [
        {
            'name': 'id',
            'value': {'stringValue': event["vendor_data"]['id']}
        }
    ]

    response = rds.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=sql,
        parameters=parameters
    )

    return response['records'][0][0]['stringValue']

def build_rds_parameters(data: dict, alias_map: dict = None):
    parameters = []

    for key, value in data.items():
        aliases = alias_map[key] if alias_map and key in alias_map else [key]

        for alias in aliases:
            param = {'name': alias}

            if value is None:
                param['value'] = {'isNull': True}
            elif isinstance(value, str):
                param['value'] = {'stringValue': value}
            elif isinstance(value, int):
                param['value'] = {'longValue': value}
            elif isinstance(value, float):
                param['value'] = {'doubleValue': value}
            elif isinstance(value, bool):
                param['value'] = {'booleanValue': value}
            else:
                raise ValueError(f"Unsupported value type for {key}")

            parameters.append(param)

    return parameters

def add_db_record(vendor_id, product_data):
    rds = boto3.client('rds-data', region_name=os.environ.get('AWS_REGION'))
    database_name = os.environ.get('DB_NAME')
    cluster_arn = os.environ.get('DB_CLUSTER_ARN')
    secret_arn = os.environ.get('DB_SECRET_ARN')
    if not all([database_name, cluster_arn, secret_arn]):
        raise ValueError("One or more RDS environment variables are not set")
    
    sql = f"""
        INSERT INTO `{database_name}`.products (vendor_id, description, sku, name, price)
        SELECT * FROM (
            SELECT :vendor_id_insert, :description, :sku_insert, :name, :price
        ) AS tmp
        WHERE NOT EXISTS (
            SELECT 1 FROM `{database_name}`.products
            WHERE sku = :sku_check AND vendor_id = :vendor_id_check
        ) LIMIT 1;
        """
    product_alias_map = {
    'sku': ['sku_insert', 'sku_check'],
    'name': ['name'],
    'description': ['description'],
    'price': ['price'],
    'stock_quantity': ['stock_quantity'],
    'vendor_id': ['vendor_id_insert', 'vendor_id_check']
    }

    for product in product_data['products']:
        product_params = build_rds_parameters(product, product_alias_map)
        rds.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=sql,
            parameters=product_params
    )




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