from loader import bot
from services import SupportTicketService
from states import SupportOpenTicketStates
from utils.keyboards import close_ticket_markup, panels_markup

from aiogram.types import ParseMode

from core.config import settings


async def support_call_handler(user_id):
    if not await SupportTicketService().user_have_opened_tickets(user_id):
        await bot.send_message(user_id, 'Выберите панель:', reply_markup=panels_markup)
        await SupportOpenTicketStates.panel.set()
    else:
        await bot.send_message(user_id, "You have opened tickets. Close them before trying to open new.")


async def call_main_admin(user_id):
    await bot.send_message(
        user_id,
        f'Вы можете связаться с главным админом написав ему в личные сообщения\n'
        f'Админ 🫡: {settings.main_admin}'
    )


async def open_support_ticket(
        user_id,
        username,
        panel,
        link,
        login,
        password,
        steam_id
):
    if not await SupportTicketService().user_have_opened_tickets(user_id):
        support_ticket_token = await SupportTicketService().create_support_ticket(
            user_id,
            username,
            panel,
            link,
            login,
            password,
            steam_id
        )
        admin_message = (f"New support ticket was opened now:\n"
                         f"Link: {settings.bot_link}?start={support_ticket_token}")
        await bot.send_message(settings.admins_chat_id, admin_message, parse_mode=ParseMode.HTML)
        await bot.send_message(
            user_id,
            "Support ticket was opened. You can write messages here.",
            reply_markup=close_ticket_markup
        )
    else:
        await bot.send_message(user_id, "You have opened tickets. Close them before trying to open new.")
