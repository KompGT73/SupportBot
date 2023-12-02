from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from core.config import settings

bot = Bot(token=settings.bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)  # noqa
