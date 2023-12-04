from handlers import open_support_ticket, support_call_handler, call_main_admin
from support_middleware import SupportMiddleware
from core.config import settings

from utils.misc.bot_commands import set_default_commands

from utils.keyboards import buttons_markup, close_ticket_markup, main_menu_markup

from loader import bot, dp, types

from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram import executor

from services import SupportTicketService, UserService, AllowedUserService

from states import SupportOpenTicketStates, NotificationsStates, AllowedUserStates


async def call_back_to_main_menu(user_id, state):
    await state.finish()
    await bot.send_message(user_id, 'Возвращаем вас в главное меню ⏪')
    await bot.send_message(user_id, f'Главное меню: 🔧', reply_markup=buttons_markup)


@dp.message_handler(lambda message: message.text == "Вернуться в главное меню ⏪")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await call_back_to_main_menu(user_id, state)


@dp.message_handler(Command('support_call'))
async def support_call(message: types.Message):
    allowed_users_lst = await AllowedUserService().get_all_allowed_users()

    if '@' + message.from_user.username in allowed_users_lst:
        await bot.send_message(message.from_user.id,
                               'Вы начали процесс открытия тикета. 💬 Нажав на кнопку'
                               ' "Вернуться в главное меню ⏪" вы можете прервать'
                               ' этот процесс и вернуться в главное меню.',
                               reply_markup=main_menu_markup)
        await support_call_handler(message.from_user.id)
    else:
        await bot.send_message(message.from_user.id, 'У вас нету доступа к данной функции! ❌')


@dp.callback_query_handler(state=SupportOpenTicketStates.panel)
async def choose_panel_query_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    if callback_query.data == 'faker-panel':
        await state.update_data(panel='Faker')
    elif callback_query.data == 'back_to_main':
        await call_back_to_main_menu(user_id, state)
        return
    else:
        await state.update_data(panel='Trump')
    await SupportOpenTicketStates.link.set()
    await bot.send_message(user_id, 'Введите ссылку 🔗:')


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'back_to_main',
                           state='*')
async def return_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await call_back_to_main_menu(user_id, state)


@dp.message_handler(state=SupportOpenTicketStates.link)
async def get_link(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    await state.update_data(link=message.text)
    await SupportOpenTicketStates.login.set()
    await bot.send_message(user_id, 'Введите логин 👤:')


@dp.message_handler(state=SupportOpenTicketStates.login)
async def get_login(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(login=message.text)
    await SupportOpenTicketStates.password.set()
    await bot.send_message(user_id, 'Введите пароль 🔑:')


@dp.message_handler(state=SupportOpenTicketStates.password)
async def get_password(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(password=message.text)
    await SupportOpenTicketStates.steam_id.set()
    await bot.send_message(user_id, 'Введите SteamID 🆔:')


@dp.message_handler(state=SupportOpenTicketStates.steam_id)
async def get_steam_id_and_open_ticket(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(steam_id=message.text)
    data = await state.get_data()
    await state.finish()
    await open_support_ticket(
        user_id,
        message.from_user.username,
        data['panel'],
        data['link'],
        data['login'],
        data['password'],
        data['steam_id']
    )


@dp.callback_query_handler()
async def callback_query_handler(callback_query: types.CallbackQuery, state: FSMContext):
    allowed_users = await AllowedUserService().get_all_allowed_users()
    print(callback_query)

    if '@' + callback_query.from_user.username in allowed_users:
        if callback_query.data == 'open-support-ticket':
            await bot.send_message(callback_query.from_user.id,
                                   'Вы начали процесс открытия тикета. 💬 Нажав на кнопку'
                                   ' "Вернуться в главное меню ⏪" вы можете прервать'
                                   ' этот процесс и вернуться в главное меню.',
                                   reply_markup=main_menu_markup)
            await support_call_handler(callback_query.from_user.id)
        elif callback_query.data == 'call_main_admin':
            await call_main_admin(callback_query.from_user.id)
        elif callback_query.data == 'back_to_main':
            await call_back_to_main_menu(callback_query.from_user.id, state)
    else:
        await bot.send_message(callback_query.from_user.id, 'У вас нету доступа к данной функции! ❌')


@dp.message_handler(Command('main_admin'))
async def call_main_admin_command(message: types.Message):
    allowed_users_lst = await AllowedUserService().get_all_allowed_users()

    if '@' + message.from_user.username in allowed_users_lst:
        await call_main_admin(message.from_user.id)
    else:
        await bot.send_message(message.from_user.id, 'У вас нету доступа к данной функции! ❌')


@dp.message_handler(lambda message: message.text == "Закрыть тикет ❎")
async def close_ticket(message: types.Message):
    user_id = message.from_user.id

    await bot.send_message(user_id, 'Закрываем тикет ✖️', reply_markup=ReplyKeyboardRemove())

    response_data = await SupportTicketService().close_user_ticket(user_id)
    if response_data.error is not None:
        await bot.send_message(user_id, response_data.error)
        return

    if response_data.opponent_id is not None:
        await bot.send_message(
            response_data.opponent_id,
            'Тикет успешно закрыт вашим оппонентом ✅',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )
        ticket_data = response_data.data
        ticket_info_text = (f'Тикет: {response_data.ticket_token}\n'
                            f'Пользователь: @{ticket_data["user_username"]}\n'
                            f'Администратор: @{ticket_data["admin_username"]}\n'
                            f'Тикет закрыт: {ticket_data["closed"]}\n\n'
                            f'Данные пользователя:\n\n'
                            f'Панель: {ticket_data["panel"]}\n'
                            f'Ссылка: {ticket_data["link"]}\n'
                            f'Логин: {ticket_data["login"]}\n'
                            f'Пароль: {ticket_data["password"]}\n'
                            f'SteamID: {ticket_data["steam_id"]}')
        await bot.send_message(settings.tickets_ends_chat_id, ticket_info_text)
    await bot.send_message(user_id, f"{response_data.message}")


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    start_support_token = message.get_args()

    if len(start_support_token) > 0:
        if await SupportTicketService().user_have_opened_tickets(user_id):
            await bot.send_message(
                user_id,
                'Вы не можете присоединиться пока у вас есть открытые тикеты! ❌'
            )
            return

        ticket_available = await SupportTicketService().check_ticket_available(start_support_token)
        if ticket_available is not None:
            await bot.send_message(user_id, ticket_available.error)
            return
        else:
            await SupportTicketService().add_admin_to_ticket(
                user_id,
                message.from_user.username,
                start_support_token
            )
            ticket_data = await SupportTicketService().get_current_ticket_data(user_id)
            await bot.send_message(ticket_data['user_id'], 'Администратор 👨‍💻 присоединился к чату')
            await message.answer(f'Вы присоединились к чату с пользователем 👤\n\n'
                                 f'Данные пользователя:\n\n'
                                 f'Панель: {ticket_data["panel"]}\n'
                                 f'Ссылка: {ticket_data["link"]}\n'
                                 f'Логин: {ticket_data["login"]}\n'
                                 f'Пароль: {ticket_data["password"]}\n'
                                 f'SteamID: {ticket_data["steam_id"]}',
                                 reply_markup=close_ticket_markup)
    else:
        await message.answer(f'Добро пожаловать в нашу тех поддержку 👨‍🔧', reply_markup=buttons_markup)


@dp.message_handler(lambda message: message.text and message.text.startswith('/ticket'))
async def get_ticket_by_token(message: types.Message):
    user_id = message.from_user.id
    if user_id == settings.main_admin_id:
        ticket_token = message.text.replace('/ticket', '').strip()

        ticket_data = await SupportTicketService().get_ticket_data_by_token(ticket_token)
        if ticket_data.error is not None:
            await bot.send_message(user_id, ticket_data.error)
            return

        ticket_info_text = (f'Тикет: {ticket_token}\n'
                            f'Пользователь: @{ticket_data.data["user_username"]}\n'
                            f'Администратор: @{ticket_data.data["admin_username"]}\n'
                            f'Тикет закрыт: {ticket_data.data["closed"]}\n\n'
                            f'Данные пользователя:\n\n'
                            f'Панель: {ticket_data.data["panel"]}\n'
                            f'Ссылка: {ticket_data.data["link"]}\n'
                            f'Логин: {ticket_data.data["login"]}\n'
                            f'Пароль: {ticket_data.data["password"]}\n'
                            f'SteamID: {ticket_data.data["steam_id"]}')
        await bot.send_message(user_id, ticket_info_text)
        for message_id in ticket_data.data['messages']:
            await bot.forward_message(
                user_id,
                from_chat_id=settings.bot_messages_chat_id,
                message_id=message_id
            )
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


@dp.message_handler(lambda message: message.text and message.text.startswith('/send_notifications'))
async def get_notifications_text(message: types.Message):
    user_id = message.from_user.id
    if user_id == settings.main_admin_id:
        await bot.send_message(user_id, 'Введите текст уведомления 💬:')
        await NotificationsStates.notification.set()
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


@dp.message_handler(state=NotificationsStates.notification, content_types=types.ContentType.ANY)
async def send_notifications(message: types.Message, state: FSMContext):
    await state.finish()
    message_id = message.message_id
    ids = await UserService().get_all_users_ids()
    for usr_id in ids:
        await bot.copy_message(usr_id, message.from_user.id, message_id)
    await bot.send_message(message.from_user.id, 'Уведомление было успешно отправлено всем пользователям! 🎉')


@dp.message_handler(lambda message: message.text and message.text.startswith('/add_allowed_user'))
async def get_allowed_user_username_to_add(message: types.Message):
    user_id = message.from_user.id

    if user_id == settings.main_admin_id:
        await bot.send_message(user_id, 'Введите ник пользователя чтобы добавить его в список: 👤')
        await AllowedUserStates.allowed_user.set()
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


@dp.message_handler(state=AllowedUserStates.allowed_user)
async def add_allowed_user(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id

    if user_id == settings.main_admin_id:
        response_data = await AllowedUserService().insert_allowed_user(message.text)
        if response_data is not None and response_data.error is not None:
            await bot.send_message(user_id, response_data.error)
            return
        await bot.send_message(user_id, f'Пользователь с ником {message.text} был успешно добавлен в список! ✅')
        return
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


@dp.message_handler(lambda message: message.text and message.text.startswith('/remove_allowed_user'))
async def get_username_to_remove_from_allowed(message: types.Message):
    user_id = message.from_user.id

    if user_id == settings.main_admin_id:
        await bot.send_message(user_id, 'Введите ник пользователя чтобы удалить его из списка: 👤')
        await AllowedUserStates.remove_allowed_user.set()
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


@dp.message_handler(state=AllowedUserStates.remove_allowed_user)
async def remove_allowed_user(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id

    if user_id == settings.main_admin_id:
        response_data = await AllowedUserService().delete_allowed_user(message.text)
        if response_data is not None and response_data.error is not None:
            await bot.send_message(user_id, response_data.error)
            return
        await bot.send_message(user_id, f'Пользователь с ником {message.text} был успешно удален из списка! ✅')
        return
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


@dp.message_handler(lambda message: message.text and message.text.startswith('/allowed_users'))
async def get_allowed_users(message: types.Message):
    user_id = message.from_user.id

    if user_id == settings.main_admin_id:
        users_lst = await AllowedUserService().get_all_allowed_users()
        users_txt = ''

        first_user = True
        for user in users_lst:
            comma = ', '
            users_txt += comma if not first_user else ''
            users_txt += user
            first_user = False

        await bot.send_message(user_id, f'Список разрешенных пользователей: 👤\n\n{users_txt}')
    else:
        await bot.send_message(user_id, 'Данную команду может исполнить только главный администратор! ❌')


async def on_startup(dispatcher):
    await set_default_commands(dispatcher)


if __name__ == '__main__':
    dp.middleware.setup(SupportMiddleware())
    executor.start_polling(dp, on_startup=on_startup)
