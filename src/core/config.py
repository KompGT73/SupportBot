from pydantic_settings import BaseSettings
from pydantic import Field

from dotenv import load_dotenv

load_dotenv()


class DBSettings(BaseSettings):
    database_url: str = Field(
        'postgresql+asyncpg://postgres:password@localhost:5432/db_name?async_fallback=true',
        json_schema_extra={'env': 'DATABASE_URL'}
    )
    db_name: str = Field('db_name', json_schema_extra={'env': 'DB_NAME'})
    db_user: str = Field('user', json_schema_extra={'env': 'DB_USER'})
    db_password: str = Field('password', json_schema_extra={'env': 'DB_PASSWORD'})
    db_host: str = Field('localhost', json_schema_extra={'env': 'DB_HOST'})
    db_port: str = Field('5432', json_schema_extra={'env': 'DB_PORT'})


class MainSettings(BaseSettings):
    bot_token: str = Field('bot_token', json_schema_extra={'env': 'BOT_TOKEN'})
    main_admin_id: int = Field('main_admin_id', json_schema_extra={'env': 'MAIN_ADMIN_ID'})
    bot_link: str = Field('bot_link', json_schema_extra={'env': 'BOT_LINK'})
    main_admin: str = Field('main_admin', json_schema_extra={'env': 'MAIN_ADMIN'})
    admins_chat_id: int = Field(
        'admins_chat_id',
        json_schema_extra={'env': 'ADMINS_CHAT_ID'}
    )
    tickets_ends_chat_id: int = Field(
        'tickets_ends_chat_id',
        json_schema_extra={'env': 'TICKETS_ENDS_CHAT_ID'}
    )
    bot_messages_chat_id: int = Field(
        'bot_messages_chat_id',
        json_schema_extra={'env': 'BOT_MESSAGES_CHAT_ID'}
    )

    # DATABASE
    db: DBSettings = Field(default_factory=DBSettings)


settings = MainSettings()
