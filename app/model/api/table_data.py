from app.common.api_models import BaseApiModel
from typing import Optional


class TableData(BaseApiModel):
    networkId: int = 4
    page: int = 1
    itemsPerPage: int = 5
    sortBy: Optional[str] = ""
    sortDesc: bool = False
    searchData: Optional[dict] = None
