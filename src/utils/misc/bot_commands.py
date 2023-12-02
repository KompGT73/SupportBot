from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="support_call", description="Обратиться в саппорт"),
        types.BotCommand(command="main_admin", description="Главный админ")
    ])
