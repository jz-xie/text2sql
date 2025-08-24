import json

import boto3


def get_secretsmanager_password(aws_secretsmanager_secret_id: str) -> str:
    session = boto3.Session()
    # Create a Secrets Manager client
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=aws_secretsmanager_secret_id
        )
        secret = get_secret_value_response["SecretString"]
        password = json.loads(secret)["password"]
        return password
    except Exception as e:
        raise ValueError(f"Error retrieving secret: {e}")
