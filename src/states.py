from aiogram.dispatcher.filters.state import StatesGroup, State


class SupportOpenTicketStates(StatesGroup):
    choosing_panel = State()
    panel = State()
    link = State()
    login = State()
    password = State()
    steam_id = State()
    ready_to_open_ticket = State()


class NotificationsStates(StatesGroup):
    notification = State()
