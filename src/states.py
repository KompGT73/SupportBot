from aiogram.dispatcher.filters.state import StatesGroup, State


class SupportOpenTicketStates(StatesGroup):
    choosing_panel = State()
    panel = State()
    link = State()
    login = State()
    password = State()
    steam_id = State()
    ready_to_open_ticket = State()
    go_to_main_menu = State()


class NotificationsStates(StatesGroup):
    notification = State()


class AllowedUserStates(StatesGroup):
    allowed_user = State()
    remove_allowed_user = State()
