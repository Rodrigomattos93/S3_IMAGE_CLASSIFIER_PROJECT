import json
import boto3
import base64
import os
import mimetypes

def lambda_handler(event, context):
    print("Lambda iniciou")

    try:
        # variaveis de ambiente na AWS
        bucket = os.environ['BUCKET_NAME']
        table_name = os.environ['DYNAMODB_TABLE']
        print(f"Bucket destino: {bucket}")
        print(f"Tabela DynamoDB: {table_name}")

        # Extrai os campos diretamente do evento
        file_content_base64 = event.get('file_content')
        object_name = event.get('object_name')

        if not file_content_base64 or not object_name:
            raise ValueError("Campos 'file_content' ou 'object_name' ausentes")

        # Decodifica imagem
        file_content = base64.b64decode(file_content_base64)
        file_path = '/tmp/tempfile'
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Detecta Content-Type
        content_type, _ = mimetypes.guess_type(object_name)
        if content_type is None:
            content_type = 'application/octet-stream'

        # Upload da imagem para o S3
        s3_client = boto3.client('s3')
        s3_client.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=object_name,
            ExtraArgs={'ContentType': content_type}
        )
        print(f"Upload realizado: s3://{bucket}/{object_name}")

        # Detecta labels com Rekognition
        rekognition_client = boto3.client('rekognition')
        rekognition_response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': object_name
                }
            },
            MaxLabels=3,
            MinConfidence=90
        )

        labels = [label['Name'] for label in rekognition_response['Labels']]
        print(f"Labels detectadas: {labels}")

        # Salva as labels no DynamoDB
        dynamodb = boto3.client('dynamodb')
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'image_name': {'S': object_name},
                'labels': {'SS': labels}
            }
        )
        print("Labels gravadas no DynamoDB com sucesso.")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'mensagem': 'Upload realizado com sucesso!',
                'labels': labels
            })
        }

    except Exception as e:
        print(f"Erro: {str(e)}")

        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(f'Erro ao fazer upload: {str(e)}')
        }
