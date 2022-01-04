from fastapi import APIRouter, Depends
from web3 import Web3
from app.common.db_models import DbChainEvent
from app.common.dependencies import no_cache
from app.model.api.chain_event import ChainEvent, ChainEventPage
from app.model.api.table_data import TableData
from app.model.api.user import User
from app.router.auth import get_current_active_user

chain_events_router = APIRouter()


@chain_events_router.post("/chain_events", status_code=200,
                          operation_id="getChainEvents",
                          response_model=ChainEventPage,
                          dependencies=[Depends(no_cache)])
async def get_chain_events(table_data: TableData, current_user: str = Depends(get_current_active_user)):
    chain_events = DbChainEvent.query.filter(DbChainEvent.network_id == table_data.networkId)

    if table_data.sortBy == "userAddress":
        if table_data.sortDesc:
            chain_events = chain_events.order_by(DbChainEvent.user_address.desc())
        else:
            chain_events = chain_events.order_by(DbChainEvent.user_address.asc())

    if table_data.sortBy == "amount":
        if table_data.sortDesc:
            chain_events = chain_events.order_by(DbChainEvent.amount.desc())
        else:
            chain_events = chain_events.order_by(DbChainEvent.amount.asc())

    if table_data.sortBy == "currency":
        if table_data.sortDesc:
            chain_events = chain_events.order_by(DbChainEvent.currency.desc())
        else:
            chain_events = chain_events.order_by(DbChainEvent.currency.asc())

    if table_data.sortBy == "name":
        if table_data.sortDesc:
            chain_events = chain_events.order_by(DbChainEvent.name.desc())
        else:
            chain_events = chain_events.order_by(DbChainEvent.name.asc())

    if table_data.sortBy == "created":
        if table_data.sortDesc:
            chain_events = chain_events.order_by(DbChainEvent.created.desc())
        else:
            chain_events = chain_events.order_by(DbChainEvent.created.asc())

    if table_data.searchData:
        if table_data.searchData["column"] == "userAddress":
            chain_events = chain_events.filter(DbChainEvent.user_address == table_data.searchData["value"])
        if table_data.searchData["column"] == "amount":
            chain_events = chain_events.filter(DbChainEvent.amount == Web3.toWei(table_data.searchData["value"], "ether"))

    chain_events_page = ChainEventPage
    chain_events_page.chainEvents = chain_events.offset((table_data.page - 1) * table_data.itemsPerPage).limit(
        table_data.itemsPerPage).all()
    chain_events_page.total = chain_events.count()
    return chain_events_page


@chain_events_router.get("/chain_event/{id}", status_code=200,
                         operation_id="getChainEvent",
                         response_model=ChainEvent,
                         dependencies=[Depends(no_cache)])
async def get_chain_event(id: str, current_user: str = Depends(get_current_active_user)):
    chain_event = DbChainEvent.where(id=id).first()
    return chain_event
