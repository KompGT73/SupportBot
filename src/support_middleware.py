from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types

from loader import bot

from services import SupportTicketService

from core.config import settings


def can_ignore_message_text(text):
    ignore_text_list = [
        '/support', 'Close Ticket', 'start', '/help', '/main_admin', 'Закрыть тикет ❎'
    ]
    for word in ignore_text_list:
        if word in text:
            return True
    return False


class SupportMiddleware(BaseMiddleware):

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.text is not None and can_ignore_message_text(message.text):
            return

        user_id = message.from_user.id
        current_ticket_data = await SupportTicketService().get_current_ticket_data(user_id)
        if current_ticket_data is None:
            return

        if current_ticket_data['is_admin']:
            await message.copy_to(current_ticket_data['user_id'])

            forwarded_message = await message.forward(settings.bot_messages_chat_id)

            await SupportTicketService().add_message_to_ticket_messages(
                message_id=forwarded_message.message_id,
                username=message.from_user.username,
                ticket_token=current_ticket_data['token']
            )
        else:
            if current_ticket_data['admin_id'] is None:
                await bot.send_message(user_id, 'The administration has not yet joined the chat')
            else:
                await message.copy_to(current_ticket_data['admin_id'])

                forwarded_message = await message.forward(settings.bot_messages_chat_id)

                await SupportTicketService().add_message_to_ticket_messages(
                    message_id=forwarded_message.message_id,
                    username=message.from_user.username,
                    ticket_token=current_ticket_data['token']
                )
        return
