from dynaconf import settings
from fastapi import APIRouter, Depends
from web3 import Web3
from app.common.api_models import Withdraw, WithdrawPage, WithdrawApproveData, WithdrawActionResult, WithdrawRejectData, \
    User
from app.common.db_models import DbWithdraw, DbLog
from app.common.dependencies import no_cache
from app.common.enums import SocketEvents, WithdrawStatus
from app.model.api.table_data import TableData
from app.router.auth import get_current_active_user

withdraw_requests_router = APIRouter()


@withdraw_requests_router.post("/withdraw_requests", status_code=200,
                               operation_id="getWithdrawRequests",
                               response_model=WithdrawPage,
                               dependencies=[Depends(no_cache)])
async def get_withdraw_requests(table_data: TableData, current_user: str = Depends(get_current_active_user)):
    withdraws = DbWithdraw.query.filter(DbWithdraw.network_id == table_data.networkId)

    if table_data.sortBy == "userAddress":
        if table_data.sortDesc:
            withdraws =withdraws.order_by(DbWithdraw.user_address.desc())
        else:
            withdraws = withdraws.order_by(DbWithdraw.user_address.asc())

    if table_data.sortBy == "amount":
        if table_data.sortDesc:
            withdraws = withdraws.order_by(DbWithdraw.amount.desc())
        else:
            withdraws = withdraws.order_by(DbWithdraw.amount.asc())

    if table_data.sortBy == "currency":
        if table_data.sortDesc:
            withdraws = withdraws.order_by(DbWithdraw.currency.desc())
        else:
            withdraws = withdraws.order_by(DbWithdraw.currency.asc())

    if table_data.sortBy == "created":
        if table_data.sortDesc:
            withdraws = withdraws.order_by(DbWithdraw.created.desc())
        else:
            withdraws = withdraws.order_by(DbWithdraw.created.asc())

    if table_data.searchData:
        if table_data.searchData["column"] == "userAddress":
            withdraws = withdraws.filter(DbWithdraw.user_address == table_data.searchData["value"])
        if table_data.searchData["column"] == "amount":
            withdraws = withdraws.filter(DbWithdraw.amount == Web3.toWei(table_data.searchData["value"], "ether"))

    withdraw_page = WithdrawPage
    withdraw_page.withdraws = withdraws.offset((table_data.page - 1) * table_data.itemsPerPage).limit(
        table_data.itemsPerPage).all()
    withdraw_page.total = withdraws.count()
    return withdraw_page


@withdraw_requests_router.get("/withdraw_request/{id}", status_code=200,
                              operation_id="getWithdrawRequest",
                              response_model=Withdraw,
                              dependencies=[Depends(no_cache)])
async def get_withdraw_request(id: str, current_user: str = Depends(get_current_active_user)):
    withdraw_request = DbWithdraw.where(id=id).first()
    return withdraw_request


@withdraw_requests_router.post("/withdraw_request/{id}", status_code=200,
                               operation_id="creatWithdrawRequest",
                               response_model=Withdraw,
                               dependencies=[Depends(no_cache)])
async def update_withdraw_request(id: str, current_user: str = Depends(get_current_active_user)):
    withdraw_request = DbWithdraw.where(id=id).first()
    return withdraw_request


@withdraw_requests_router.put("/withdraw_request/{id}", status_code=200,
                              operation_id="getWithdrawRequests",
                              response_model=Withdraw,
                              dependencies=[Depends(no_cache)])
async def create_withdraw_request(id: str, current_user: str = Depends(get_current_active_user)):
    withdraw_request = DbWithdraw.where(id=id).first()
    return withdraw_request


@withdraw_requests_router.post("/approve_withdraw_request", status_code=200,
                               operation_id="approveWithdrawRequest",
                               response_model=WithdrawActionResult,
                               dependencies=[Depends(no_cache)])
def approve_withdraw_request(withdraw_approve_data: WithdrawApproveData, current_user: str = Depends(get_current_active_user)):
    withdraw_id = withdraw_approve_data.id
    withdraw = DbWithdraw.where(id=withdraw_id).first()
    withdraw_action_result = WithdrawActionResult
    withdraw_action_result.user_address = withdraw_approve_data.user_address
    withdraw_action_result.id = withdraw_approve_data.id
    if withdraw.status == WithdrawStatus.PENDING:
        if settings.NETWORKS[withdraw.network_id].ADMIN.lower() == withdraw_approve_data.user_address.lower():
            withdraw.approve(withdraw_approve_data.signature)
            DbWithdraw.session.commit()
            withdraw.user.emit(SocketEvents.WITHDRAW_STATE_CHANGED, Withdraw.from_orm(withdraw))
            withdraw.user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(withdraw.user))
            withdraw_action_result.success = True
        else:
            withdraw_action_result.message = f"Withdraw {withdraw.id} from {withdraw.user_address} for {withdraw.amount / 10 ** 18} {withdraw.currency} approve fail. You ({withdraw_approve_data.user_address}) not admin {settings.NETWORKS[withdraw.network_id].ADMIN.lower()}  in this network ({withdraw.network_id}). "
            DbLog.create(network_id=withdraw.network_id, log_description=withdraw_action_result.message)
            DbLog.session.commit()
    else:
        withdraw_action_result.message = f"Withdraw {withdraw.id} from {withdraw.user_address} for {withdraw.amount / 10 ** 18} {withdraw.currency} approve fail. Withdraw status {withdraw.status}"
        DbLog.create(network_id=withdraw.network_id, log_description=withdraw_action_result.message)
        DbLog.session.commit()

    return withdraw_action_result


@withdraw_requests_router.post("/reject_withdraw_request", status_code=200,
                               operation_id="rejectWithdrawRequest",
                               response_model=WithdrawActionResult,
                               dependencies=[Depends(no_cache)])
def reject_withdraw_request(withdraw_reject_data: WithdrawRejectData, current_user: str = Depends(get_current_active_user)):
    withdraw_id = withdraw_reject_data.id
    withdraw = DbWithdraw.where(id=withdraw_id).first()
    withdraw_action_result = WithdrawActionResult
    withdraw_action_result.user_address = withdraw_reject_data.user_address
    withdraw_action_result.id = withdraw_reject_data.id
    if withdraw.status == WithdrawStatus.PENDING or withdraw.status == WithdrawStatus.APPROVED:
        withdraw.reject(withdraw_reject_data.reject_message)
        DbWithdraw.session.commit()
        withdraw_action_result.success = True
        withdraw_action_result.message = f"Withdraw {withdraw.id} from {withdraw.user_address}"
        f"for {withdraw.amount / 10 ** 18} {withdraw.currency} rejected"
        withdraw.user.emit(SocketEvents.WITHDRAW_STATE_CHANGED, Withdraw.from_orm(withdraw))
        withdraw.user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(withdraw.user))
    else:
        withdraw_action_result.message = f"Withdraw {withdraw.id} from {withdraw.user_address} "
        f"for {withdraw.amount / 10 ** 18} {withdraw.currency} reject fail. Withdraw status {withdraw.status}"

    return withdraw_action_result
