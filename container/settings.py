from pydantic import BaseSettings


class Settings(BaseSettings):
    PORT: int

    PHOTOS_BUCKET: str
    FACES_BUCKET: str
    DB_ENDPOINT: str
    DB_PATH: str
    DB_NAME: str = 'photo'

    LOG_LEVEL: str = 'INFO'
    LOGGER_NAME: str = 'container_logger'
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s %(pathname)s %(lineno)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': LOG_LEVEL,
            },
        },
        'loggers': {
            LOGGER_NAME: {
                'handlers': ['console'],
                'level': LOG_LEVEL,
            },
        }
    }


settings = Settings()
