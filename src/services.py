from core.database import async_session_maker
from utils.tokens import generate_token
from models import SupportTicket, TicketMessages, User, AllowedUser
from dataclasses_ import ResponseData

from sqlalchemy import select, exists, insert, or_, and_, false, update, delete

from core.config import settings


class BaseService:

    def __init__(self):
        self.session = async_session_maker()


class AllowedUserService(BaseService):

    async def allowed_user_exists(self, username: str):
        async with self.session.begin():
            stmt = exists(AllowedUser).where(AllowedUser.username == username).select()
            res = await self.session.execute(stmt)
            return res.scalar()

    async def insert_allowed_user(self, username):
        user_exists = await self.allowed_user_exists(username)
        if user_exists:
            return ResponseData(error='Этот ник уже есть в списке разрешенных пользователей. '
                                      'Вы не можете добавить его повторно! ❌')

        async with self.session.begin():
            stmt = insert(AllowedUser).values(username=username)
            await self.session.execute(stmt)
            await self.session.commit()

    async def delete_allowed_user(self, username):
        user_exists = await self.allowed_user_exists(username)
        if not user_exists:
            return ResponseData(
                error='Этого ника нету в списке разрешенных пользователей! ❌'
            )

        async with self.session.begin():
            stmt = delete(AllowedUser).where(AllowedUser.username == username)
            await self.session.execute(stmt)
            await self.session.commit()

    async def get_all_allowed_users(self) -> list[str]:
        allowed_usernames = []

        async with self.session.begin():
            stmt = select(AllowedUser)
            res = await self.session.execute(stmt)
            users = res.fetchall()
            for user in users:
                user = user[0]
                allowed_usernames.append(user.username)

        return allowed_usernames


class UserService(BaseService):

    async def get_all_users_ids(self) -> list:
        async with self.session.begin():
            ids_list = []
            stmt = select(User.user_id).where(User.id.notin_([settings.admin_id]))
            res = await self.session.execute(stmt)
            for obj_id in res.fetchall():
                ids_list.append(obj_id[0])
            return ids_list

    async def user_id_exists(self, user_id):
        stmt = exists(User).where(User.user_id == user_id).select()
        res = await self.session.execute(stmt)
        return res.scalar()

    async def insert_user_id_without_commit(self, user_id):
        async with self.session.begin():
            if not await self.user_id_exists(user_id):
                stmt = insert(User).values(user_id=user_id)
                await self.session.execute(stmt)


class SupportTicketService(BaseService):

    async def check_exists_by_token(self, token: str):
        async with self.session.begin():
            stmt = exists(SupportTicket).where(SupportTicket.token == token).select()
            res = await self.session.execute(stmt)
            return res.scalar()

    async def create_support_ticket(
            self,
            user_id,
            user_username,
            panel,
            link,
            login,
            password,
            steam_id
    ) -> str:
        token = generate_token()
        while await self.check_exists_by_token(token):
            token = generate_token()
        async with self.session.begin():
            stmt = insert(SupportTicket).values(
                user_id=user_id,
                token=token,
                user_username=user_username,
                panel=panel,
                link=link,
                login=login,
                password=password,
                steam_id=steam_id
            )
            await self.session.execute(stmt)
            await UserService().insert_user_id_without_commit(user_id)
            await self.session.commit()
        return token

    async def user_have_opened_tickets(self, user_id):
        async with self.session.begin():
            stmt = exists(SupportTicket).where(
                or_(
                    and_(
                        SupportTicket.user_id == user_id,
                        SupportTicket.closed == false()
                    ),
                    and_(
                        SupportTicket.admin_id == user_id, SupportTicket.closed == false()
                    )
                )
            ).select()
            res = await self.session.execute(stmt)
            return res.scalar()

    async def get_active_ticket_for_user(self, user_id):
        stmt = select(SupportTicket).filter_by(user_id=user_id, closed=False)
        res = await self.session.execute(stmt)
        return res.scalar()

    async def user_ticket_have_admin(self, ticket: SupportTicket):
        async with self.session.begin():
            # user_active_ticket = await self.get_active_ticket_for_user(user_id)
            if ticket.admin_id is not None:
                return True
            return False

    async def get_ticket_by_token(self, token: str):
        stmt = select(SupportTicket).where(SupportTicket.token == token)
        res = await self.session.execute(stmt)
        return res.scalar()

    async def get_ticket_as_admin(self, user_id):
        """Returns active ticket or None for admin user"""
        stmt = select(SupportTicket).filter_by(admin_id=user_id, closed=False)
        res = await self.session.execute(stmt)
        return res.scalar()

    @staticmethod
    async def user_in_ticket_close_request_ids(ticket, user_id):
        requests_ids = ticket.close_requests_ids
        print(requests_ids)
        print(user_id)
        if str(user_id) in requests_ids:
            return True
        return False

    async def admin_in_another_ticket(self, user_id):
        async with self.session.begin():
            ticket = await self.get_ticket_as_admin(user_id)
            if ticket is None:
                return False
            return True

    async def update_ticket_close_requests(self, ticket, user_id):
        stmt = update(SupportTicket).where(SupportTicket.id == ticket.id).values(close_requests_ids=[user_id])
        await self.session.execute(stmt)

    async def close_user_ticket(self, user_id) -> ResponseData:
        async with self.session.begin():
            ticket = await self.get_active_ticket_for_user(user_id) or await self.get_ticket_as_admin(user_id)

            if ticket is not None:
                ticket_already_closed = False

                default_response_data = ResponseData(
                    message='Вы успешно закрыли этот тикет! ✅',
                    ticket_closed=True
                )

                if ticket.admin_id is None:
                    if ticket.close_requests >= 1:
                        return ResponseData(
                            error='Этот тикет уже закрыт! ❌'
                        )
                    response_data = default_response_data
                elif ticket.admin_id is not None:
                    opponent_id = ticket.admin_id if ticket.admin_id != user_id else ticket.user_id

                    if await self.user_in_ticket_close_request_ids(ticket, user_id):
                        return ResponseData(error='Вы уже проголосовали за закрытие тикета! ❌'
                                                  ' Пожалуйста, подождите своего оппонента.')

                    if ticket.close_requests < 1:

                        response_data = ResponseData(
                            message=(f'Вы хотите закрыть тикет'
                                     f'\nЗапросы на закрытие тикета: 1/2'),
                            ticket_closed=False,
                            opponent_id=opponent_id
                        )
                    else:
                        response_data = default_response_data
                        response_data.opponent_id = opponent_id
                        response_data.data = {
                            'user_username': ticket.user_username,
                            'admin_username': ticket.admin_username,
                            'closed': True,
                            'panel': ticket.panel,
                            'link': ticket.link,
                            'login': ticket.login,
                            'password': ticket.password,
                            'steam_id': ticket.steam_id
                        }

                if response_data.ticket_closed:
                    ticket.closed = True

                response_data.ticket_token = ticket.token
                if not ticket_already_closed:
                    ticket.close_requests += 1
                ticket.close_requests_ids.append(str(user_id))
                # await self.update_ticket_close_requests(ticket, user_id)
                await self.session.commit()
                return response_data
            else:
                return ResponseData(
                    error='Этот тикет был закрыт либо он не существует! ❌'
                )

    async def get_current_ticket_data(self, user_id) -> dict | None:
        async with self.session.begin():
            ticket_data = {}
            ticket = await self.get_ticket_as_admin(user_id)
            ticket_data['is_admin'] = True

            if ticket is None:
                ticket = await self.get_active_ticket_for_user(user_id)
                if ticket is None:
                    return None
                ticket_data['is_admin'] = False

            ticket_data['admin_id'] = ticket.admin_id
            ticket_data['user_id'] = ticket.user_id
            ticket_data['token'] = ticket.token
            new_ticket_data = {
                'panel': ticket.panel,
                'link': ticket.link,
                'login': ticket.login,
                'password': ticket.password,
                'steam_id': ticket.steam_id
            }
            ticket_data.update(new_ticket_data)
            return ticket_data

    async def get_ticket_data_by_token(self, ticket_token):
        async with self.session.begin():
            ticket = await self.get_ticket_by_token(ticket_token)
            if ticket is None:
                return ResponseData(
                    error='Я не нашел тикет с данным токеном ❌'
                )

            ticket_data = {
                'admin_id': ticket.admin_id,
                'user_id': ticket.user_id,
                'user_username': ticket.user_username,
                'admin_username': ticket.admin_username,
                'closed': ticket.closed,
                'messages': [message.message_id for message in ticket.messages],
                'panel': ticket.panel,
                'link': ticket.link,
                'login': ticket.login,
                'password': ticket.password,
                'steam_id': ticket.steam_id
            }
            return ResponseData(data=ticket_data)

    async def add_admin_to_ticket(self, admin_id, admin_username, ticket_token: str):
        async with self.session.begin():
            ticket = await self.get_ticket_by_token(ticket_token)
            ticket.admin_id = admin_id
            ticket.admin_username = admin_username
            await self.session.commit()

    async def check_ticket_available(self, ticket_token):
        async with self.session.begin():
            ticket = await self.get_ticket_by_token(ticket_token)
            if ticket is None:
                return ResponseData(
                    error='Такой тикет не существует! ❌'
                )

            if ticket.closed:
                return ResponseData(
                    error='Этот тикет был закрыт! ❌'
                )

            if ticket.admin_id is not None:
                return ResponseData(
                    error='Этот уже занят другим админом! ❌'
                )
            return None

    async def create_ticket_message(self, message_id, username):
        stmt = insert(TicketMessages).values(
            message_id=message_id,
            sender_username=username
        ).returning(TicketMessages.id)
        insert_res = await self.session.execute(stmt)
        ticket_message_id = insert_res.scalar()
        message_stmt = select(TicketMessages).where(TicketMessages.id == ticket_message_id)
        res = await self.session.execute(message_stmt)
        message = res.scalar()
        return message

    async def add_message_to_ticket_messages(
            self,
            message_id,
            username,
            ticket_token: str
    ):
        async with self.session.begin():
            ticket = await self.get_ticket_by_token(ticket_token)
            message = await self.create_ticket_message(message_id, username)
            ticket.messages.append(message)
            await self.session.commit()

    async def get_ticket_messages_list(self, ticket_token: str):
        messages = []

        async with self.session.begin():
            ticket = await self.get_ticket_by_token(ticket_token)
            for message in ticket.messages:
                messages.append(
                    {
                        'text': message.message_text,
                        'username': message.sender_username
                    }
                )
        return messages
