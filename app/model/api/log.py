from datetime import datetime
from typing import List, Optional
from app.common.api_models import BaseApiModel


class Log(BaseApiModel):
    id: int
    network_id: int
    log_description: str
    created: datetime


class LogPage(BaseApiModel):
    total: int
    logs: List[Log]
