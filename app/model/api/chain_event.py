from datetime import datetime
from typing import List
from app.common.api_models import BaseApiModel
from app.common.enums import Currency


class ChainEvent(BaseApiModel):
    id: int
    transaction_hash: str
    contract_address: str
    user_address: str
    transaction_hash: str
    network_id: int
    amount: float
    name: str
    data: dict
    currency: Currency
    created: datetime


class ChainEventPage(BaseApiModel):
    total: int
    chainEvents: List[ChainEvent]
