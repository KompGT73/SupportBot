from aiogram import types

# PANELS
panels_markup = types.InlineKeyboardMarkup(row_width=2)
faker_panel_button = types.InlineKeyboardButton('Faker 1️⃣', callback_data='faker-panel')
trump_panel_button = types.InlineKeyboardButton('Trump 2️⃣', callback_data='trump-panel')

panels_markup.add(faker_panel_button, trump_panel_button)

# CLOSE TICKET

close_ticket_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
close_ticket_button = types.KeyboardButton('Закрыть тикет ❎')

close_ticket_markup.add(close_ticket_button)

# MAIN

buttons_markup = types.InlineKeyboardMarkup(row_width=5)
support_button = types.InlineKeyboardButton('Support 👨‍💻', callback_data='open-support-ticket')
call_main_admin_button = types.InlineKeyboardButton(
    'Главный админ 🫡',
    callback_data='call_main_admin'
)

buttons_markup.add(support_button, call_main_admin_button)
