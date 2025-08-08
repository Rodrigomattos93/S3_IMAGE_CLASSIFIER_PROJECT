import os
import boto3
from azure.storage.blob import BlobClient

# Cliente AWS S3
s3_client = boto3.client("s3")

# Variáveis de ambiente configuradas no Lambda
AZURE_ACCOUNT_NAME = os.environ["AZURE_ACCOUNT_NAME"]
AZURE_CONTAINER_NAME = os.environ["AZURE_CONTAINER_NAME"]
SAS_TOKEN_AZURE = os.environ["SAS_TOKEN_AZURE"]

AZURE_BLOB_URL_BASE = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER_NAME}"

def lambda_handler(event, context):
    try:
        # Extrair informações do evento do S3
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]

        print(f"Novo arquivo no S3: {object_key} (bucket: {bucket_name})")

        # Baixar o arquivo do S3 para /tmp
        local_path = f"/tmp/{os.path.basename(object_key)}"
        s3_client.download_file(bucket_name, object_key, local_path)

        print(f"Arquivo baixado para {local_path}")

        # Criar o cliente do Blob no Azure
        blob_url = f"{AZURE_BLOB_URL_BASE}/{os.path.basename(object_key)}?{SAS_TOKEN_AZURE}"
        blob_client = BlobClient.from_blob_url(blob_url)

        # Enviar o arquivo para o Azure
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        print(f"Arquivo enviado para Azure Blob Storage: {blob_url}")

        return {
            "statusCode": 200,
            "body": f"Arquivo {object_key} enviado para Azure com sucesso."
        }

    except Exception as e:
        print(f"Erro: {e}")
        return {
            "statusCode": 500,
            "body": f"Erro ao processar arquivo: {str(e)}"
        }
