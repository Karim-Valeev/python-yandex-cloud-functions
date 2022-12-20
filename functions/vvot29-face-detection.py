import base64
import json
import os

import boto3
import requests

BATCH_ANALYZE_URL = 'https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze'


def get_face_detection_request_body(content):
    return {
        'analyze_specs': [{
            'content': content,
            'features': [{
                'type': 'FACE_DETECTION'
            }]
        }]
    }


def find_faces_coordinates(photo, api_key) -> list:
    encoded = base64.b64encode(photo).decode('UTF-8')
    body = get_face_detection_request_body(encoded)
    headers = {'Authorization': f'Api-Key {api_key}'}
    response = requests.post(BATCH_ANALYZE_URL, json=body, headers=headers)
    coordinates = []
    try:
        faces = response.json()['results'][0]['results'][0]['faceDetection']['faces']
        for face in faces:
            coordinates.append(face['boundingBox']['vertices'])
    except KeyError:
        return []
    return coordinates


def create_message(photo_key: str, face: list):
    return {
        'photo_key': photo_key,
        'face': face,
    }


def send_to_queue(photo_key: str, faces: list, mq_url):
    session = boto3.session.Session()
    sqs = session.client(
        service_name='sqs',
        endpoint_url='https://message-queue.api.cloud.yandex.net',
        region_name='ru-central1'
    )
    messages = [create_message(photo_key, face) for face in faces]
    for message in messages:
        sqs.send_message(
            QueueUrl=mq_url,
            MessageBody=json.dumps(message),
            MessageDeduplicationId=photo_key
        )


def get_photo(bucket: str, photo_key: str):
    """Возвращает фотографию из бакета, если ее размер менее 1мб."""
    session = boto3.session.Session()
    s3 = session.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net')
    response = s3.get_object(Bucket=bucket, Key=photo_key)

    if int(response['ContentLength']) / (10**6) > 1:
        raise Exception('Размер фотографии превышает 1 мб!') from None

    return response['Body'].read()


def handler(event, *args, **kwargs):
    """Триггер реагирует только на .jpg файлы."""

    api_key = os.environ.get('API_SECRET_KEY')
    mq_url = os.environ.get('MQ_URL')

    bucket = event['messages'][0]['details']['bucket_id']
    photo_key = event['messages'][0]['details']['object_id']
    photo = get_photo(bucket, photo_key)
    faces = find_faces_coordinates(photo, api_key)
    send_to_queue(photo_key, faces, mq_url)
