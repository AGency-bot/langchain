import os
import json
import boto3
from botocore.exceptions import ClientError

def load_config_secret(secret_name="langchain-agent/config", fallback_path="secrets_local.json"):
    region = os.getenv("AWS_REGION", "eu-central-1")

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_str = response["SecretString"]
        return json.loads(secret_str)
    except ClientError as e:
        print(f"⚠️ AWS Secrets Manager error: {e}")
        if os.path.exists(fallback_path):
            print(f"🔁 Falling back to local file: {fallback_path}")
            with open(fallback_path, "r") as f:
                return json.load(f)
        raise RuntimeError("❌ Unable to load secrets from AWS or fallback.")
