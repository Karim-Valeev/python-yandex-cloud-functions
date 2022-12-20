import io
import json
import logging
import random
from logging.config import dictConfig

import boto3

import ydb
import ydb.iam
from PIL import Image
from sanic import Sanic
from sanic.response import empty
from settings import settings

dictConfig(settings.LOGGING)
logger = logging.getLogger(settings.LOGGER_NAME)

app = Sanic(__name__)

ydb_driver: ydb.Driver


def get_driver():
    endpoint = settings.DB_ENDPOINT
    path = settings.DB_PATH
    credentials = ydb.iam.MetadataUrlCredentials()
    driver_config = ydb.DriverConfig(
        endpoint, path, credentials=credentials
    )
    return ydb.Driver(driver_config)


@app.after_server_start
async def after_server_start(app, loop):
    logger.info('Приложение слушает на порту %s', settings.PORT)
    global ydb_driver
    ydb_driver = get_driver()
    ydb_driver.wait(timeout=5)


def get_photo(bucket: str, photo_key: str):
    session = boto3.session.Session()
    s3 = session.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net')
    response = s3.get_object(Bucket=bucket, Key=photo_key)
    return response['Body'].read()


def upload_photo(bucket, photo_key, body):
    session = boto3.session.Session()
    s3 = session.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net')
    s3.put_object(Body=body, Bucket=bucket, Key=photo_key, ContentType='application/octet-stream')


def add_photo_face_info_to_db(photo_key, photo_face_key):
    query = f"""
        PRAGMA TablePathPrefix("{settings.DB_PATH}");
        INSERT INTO {settings.DB_NAME} (id, photo_key, photo_face_key)
        VALUES ({random.getrandbits(64)}, '{photo_key}', '{photo_face_key}');
    """
    session = ydb_driver.table_client.session().create()
    session.transaction().execute(query, commit_tx=True)
    session.closing()


def handle_message(message, index):
    logger.info('Обрабатывается сообщение: %s', message)
    body = json.loads(message['details']['message']['body'])
    photo_key = body['photo_key']
    image = Image.open(io.BytesIO(get_photo(settings.PHOTOS_BUCKET, photo_key)))
    face = body['face']

    x, y = set(), set()
    for coordinate in face:
        x.add(int(coordinate['x']))
        y.add(int(coordinate['y']))
    sorted_x, sorted_y = sorted(x), sorted(y)
    left, right, top, bottom = sorted_x[0], sorted_x[1], sorted_y[0], sorted_y[1]

    photo_face_id = f"{photo_key.removesuffix('.jpg')}_{index}.jpg"
    photo_face = image.crop((left, top, right, bottom))
    img_byte_arr = io.BytesIO()
    photo_face.save(img_byte_arr, format='JPEG')

    upload_photo(settings.FACES_BUCKET, photo_face_id, img_byte_arr.getvalue())

    add_photo_face_info_to_db(photo_key, photo_face_id)


@app.post('/')
async def handle_trigger_message(request):
    logger.info('Получен запрос: %s', request.json)
    messages = request.json['messages']
    index = random.randint(1, 100)
    for message in messages:
        try:
            handle_message(message, index)
        except Exception as ex:
            logger.error(ex)
    logger.info('Сообщения обработаны')
    return empty(status=200)


@app.after_server_stop
async def shutdown():
    ydb_driver.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=settings.PORT, motd=False, access_log=False)
