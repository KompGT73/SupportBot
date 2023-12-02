from dataclasses import dataclass

from typing import Optional


@dataclass
class ResponseData:
    message: Optional[str] = None
    data: Optional[dict] = None
    ticket_closed: Optional[bool] = None
    ticket_token: Optional[str] = None
    opponent_id: Optional[str] = None
    error: Optional[str] = None
