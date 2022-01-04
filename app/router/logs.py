from fastapi import APIRouter, Depends
from app.common.db_models import DbLog
from app.common.dependencies import no_cache
from app.model.api.log import LogPage
from app.model.api.table_data import TableData
from app.router.auth import get_current_active_user
from app.model.api.user import User

logs_router = APIRouter()


@logs_router.post("/logs", status_code=200,
                  operation_id="getLogs",
                  response_model=LogPage,
                  dependencies=[Depends(no_cache)])
async def get_logs(table_data: TableData, current_user: str = Depends(get_current_active_user)):
    logs = DbLog.query.filter(DbLog.network_id == table_data.networkId)

    if table_data.sortBy == "created":
        if table_data.sortDesc:
            logs = logs.order_by(DbLog.created.desc())
        else:
            logs = logs.order_by(DbLog.created.asc())
    log_page = LogPage
    log_page.logs = logs.offset((table_data.page - 1) * table_data.itemsPerPage).limit(table_data.itemsPerPage).all()
    log_page.total = logs.count()
    return log_page
