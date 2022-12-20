import json
from typing import Optional

import telegram
import ydb
import ydb.iam
from pydantic import BaseSettings
from telegram import InputMediaPhoto

ydb_driver: ydb.Driver

START_COMMAND_TEXT = 'Этот бот может присваивать имена безымянным фотографиям.'
HELP_COMMAND_TEXT = 'Доступные команды: \n/start \n/help \n/getface \n/find {name}'


class Settings(BaseSettings):
    DB_ENDPOINT: str
    DB_PATH: str
    DB_NAME: str
    TELEGRAM_BOT_TOKEN: str
    PHOTO_FACE_LINK: str
    PHOTO_LINK: str


def get_driver(settings: Settings):
    endpoint = settings.DB_ENDPOINT
    path = settings.DB_PATH
    credentials = ydb.iam.MetadataUrlCredentials()
    driver_config = ydb.DriverConfig(
        endpoint, path, credentials=credentials
    )
    return ydb.Driver(driver_config)


def prepare_ydb_driver(settings: Settings):
    global ydb_driver
    ydb_driver = get_driver(settings)
    ydb_driver.wait(timeout=5)


def get_nameless_photo_face_url(settings: Settings) -> Optional[str]:
    query = f"""
        PRAGMA TablePathPrefix("{settings.DB_PATH}");
        SELECT * FROM {settings.DB_NAME} WHERE name is NULL LIMIT 1;
    """
    session = ydb_driver.table_client.session().create()
    result = session.transaction().execute(query, commit_tx=True)
    session.closing()
    for row in result[0].rows:
        photo_face_key = row.photo_face_key
        return settings.PHOTO_FACE_LINK % photo_face_key
    return None


def assign_name_to_last_photo_face(name: str, settings: Settings):
    query = f"""
        PRAGMA TablePathPrefix("{settings.DB_PATH}");
        SELECT * FROM {settings.DB_NAME} WHERE name is NULL LIMIT 1;
    """
    session = ydb_driver.table_client.session().create()
    result_sets = session.transaction().execute(query, commit_tx=True)
    photo_face_key = None
    for row in result_sets[0].rows:
        photo_face_key = row.photo_face_key
    if photo_face_key:
        query = f"""
            PRAGMA TablePathPrefix("{settings.DB_PATH}");
            UPDATE {settings.DB_NAME} SET name = '{name}' WHERE photo_face_key = '{photo_face_key}';
        """
        session.transaction().execute(query, commit_tx=True)
        session.closing()


def find_original_photos_urls(name, settings: Settings) -> list:
    query = f"""
        PRAGMA TablePathPrefix("{settings.DB_PATH}");
        SELECT DISTINCT photo_key, name FROM {settings.DB_NAME} WHERE name = '{name}';
    """
    session = ydb_driver.table_client.session().create()
    result_sets = session.transaction().execute(query, commit_tx=True)
    session.closing()

    photo_urls = []
    if len(result_sets[0].rows) != 0:
        for row in result_sets[0].rows:
            photo_key = row.photo_key
            photo_url = settings.PHOTO_LINK % photo_key
            photo_urls.append(photo_url)
    return photo_urls


def handler(event, *args, **kwargs):
    settings = Settings()
    prepare_ydb_driver(settings)
    telegram_bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)

    request = event['body']
    update = telegram.Update.de_json(json.loads(request), telegram_bot)
    chat_id = update.message.chat.id
    command = update.message.text.encode('utf-8').decode()

    if command == '/start':
        telegram_bot.sendMessage(chat_id=chat_id, text=START_COMMAND_TEXT)
    elif command == '/help':
        telegram_bot.sendMessage(chat_id=chat_id, text=HELP_COMMAND_TEXT)
    elif command == '/getface':
        nameless_photo_face_url = get_nameless_photo_face_url(settings)
        if nameless_photo_face_url:
            telegram_bot.send_photo(chat_id=chat_id, photo=nameless_photo_face_url)
        else:
            telegram_bot.sendMessage(chat_id=chat_id, text='Фотографий без имени не осталось')
    elif command.startswith('/find'):
        name = command.split(' ')[-1]
        photos_urls = find_original_photos_urls(name, settings)
        if photos_urls:
            telegram_bot.send_media_group(
                chat_id=chat_id,
                media=[InputMediaPhoto(photo_url) for photo_url in photos_urls]
            )
        else:
            telegram_bot.sendMessage(chat_id=chat_id, text=f'Фотографии с {name} не найдены')
    else:
        assign_name_to_last_photo_face(command, settings)
        telegram_bot.sendMessage(chat_id=chat_id, text=f'Данному лицу было присвоено имя {command}')

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'isBase64Encoded': False,
        'body': 'success'
    }
