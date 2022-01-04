from fastapi import APIRouter, Depends, HTTPException
from web3 import Web3
from app.common.api_models import User as Usr, UserPage, UserEdit
from app.common.db_models import DbUser
from app.common.dependencies import no_cache
from app.model.api.table_data import TableData
from app.model.api.user import User
from app.router.auth import get_current_active_user
from http import HTTPStatus

users_router = APIRouter()


@users_router.post("/users", status_code=200,
                   operation_id="getUsers",
                   response_model=UserPage,
                   dependencies=[Depends(no_cache)])
async def get_users(table_data: TableData, current_user: str = Depends(get_current_active_user)):
    users = DbUser.query.filter(DbUser.network_id == table_data.networkId)

    if table_data.sortBy == "address":
        if table_data.sortDesc:
            users = users.order_by(DbUser.address.desc())
        else:
            users = users.order_by(DbUser.address.asc())

    if table_data.sortBy == "ethBalance":
        if table_data.sortDesc:
            users = users.order_by(DbUser.eth_balance.desc())
        else:
            users = users.order_by(DbUser.eth_balance.asc())

    if table_data.sortBy == "usdtBalance":
        if table_data.sortDesc:
            users = users.order_by(DbUser.usdt_balance.desc())
        else:
            users = users.order_by(DbUser.usdt_balance.asc())

    if table_data.sortBy == "created":
        if table_data.sortDesc:
            users = users.order_by(DbUser.created.desc())
        else:
            users = users.order_by(DbUser.created.asc())

    if table_data.searchData:
        if table_data.searchData["column"] == "Address":
            users = users.filter(DbUser.address == table_data.searchData["value"])
        if table_data.searchData["column"] == "ETH Balance":
            users = users.filter(DbUser.eth_balance == Web3.toWei(table_data.searchData["value"], "ether"))
        if table_data.searchData["column"] == "USDT Balance":
            users = users.filter(DbUser.usdt_balance == Web3.toWei(table_data.searchData["value"], "ether"))

    user_page = UserPage
    user_page.users = users.offset((table_data.page - 1) * table_data.itemsPerPage).limit(table_data.itemsPerPage).all()
    user_page.total = users.count()
    return user_page


@users_router.get("/user/{id}", status_code=200,
                  operation_id="getUser",
                  response_model=Usr,
                  dependencies=[Depends(no_cache)])
async def get_user(id: str, current_user: str = Depends(get_current_active_user)):
    user = DbUser.where(address=id).first()
    return user


@users_router.put("/user/{user_address}", status_code=200,
                  operation_id="updateUser",
                  response_model=Usr,
                  dependencies=[Depends(no_cache)])
async def update_user(user_address: str, user_input: UserEdit, current_user: str = Depends(get_current_active_user)):
    user = DbUser.where(network_id=user_input.network_id, address=user_address).first()

    if not user:
        raise HTTPException(HTTPStatus.NOT_FOUND, "User not found")
    user.update(eth_balance=user_input.eth_balance, usdt_balance=user_input.usdt_balance)

    DbUser.session.commit()
    return user
