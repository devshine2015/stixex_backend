from http import HTTPStatus
import pendulum
from fastapi import APIRouter, Depends, HTTPException
from app.common.api_models import Bet, BetPage, BetEdit
from app.common.db_models import DbBet, Base, DbReferral, DbPool, DbUser
from app.common.dependencies import no_cache
from app.common.enums import BetResult, Currency
from app.common.utils import amount_formatter
from app.model.api.table_data import TableData
from datetime import timezone, datetime
from app.model.api.user import User
from app.model.api.win_loss import WinLoss
from app.router.auth import get_current_active_user
from dynaconf import settings
from web3 import Web3, WebsocketProvider
import json
import threading
import timeit
from sqlalchemy.sql import func
from flask import Flask, session
from itertools import groupby
from operator import itemgetter
import time
import atexit
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from web3 import Web3, WebsocketProvider
from app.common.enums import Asset, TimeFrame, WithdrawStatus, SocketEvents

bets_router = APIRouter()


def get_bets_count(**kwargs):
    return DbBet.where(**kwargs).count()


def get_users_sum(currency, name, network_id):
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(SUM(amount), 0) AS numeric), 0) from db_chain_event WHERE "
        f"name='{name}' AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    if currency == Currency.USDT:
        return (value or 0) / 10 ** 6

    return amount_formatter(value or 0)


def get_bets_amount_sum_24(currency, network_id):

    dt = pendulum.now()
    # dt = datetime.utcnow()
    dt_past_24 = dt.subtract(hours=24)
    # dt_past_24 = datetime.utcnow() - timedelta(minutes=5)

    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(SUM(ABS(amount)), 0) AS numeric), 0) from db_bet WHERE "
        f"created>'{dt_past_24}' AND "
        f"created<'{dt}' AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    print(value,"value")
    return amount_formatter(value or 0)


def get_bets_amount_sum_week(currency, network_id):
    dt = pendulum.now()
    dt_past_week = dt.subtract(days=7)
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(SUM(ABS(amount)), 0) AS numeric), 0) from db_bet WHERE "
        f"created>'{dt_past_week}' AND "
        f"created<'{dt}' AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    return amount_formatter(value or 0)


def get_bets_amount_sum_month(currency, month, network_id):
    dt = pendulum.now()
    dt_past_month = dt.subtract(months=month)
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(SUM(ABS(amount)), 0) AS numeric), 0) from db_bet WHERE "
        f"created>'{dt_past_month}' AND "
        f"created<'{dt}' AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    return amount_formatter(value or 0)


def get_bets_amount_sum(currency, result, network_id):
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(SUM(ABS(amount)), 0) AS numeric), 0) from db_bet WHERE "
        f"result='{result}' AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    return amount_formatter(value or 0)


def get_bets_fee_sum(currency, network_id):
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(SUM(fee * amount), 0) AS numeric), 0) from db_bet WHERE "
        f"fee > 0 AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    return amount_formatter(value or 0)


def get_bets_fee_avg(currency, network_id):
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(AVG(fee * amount), 0) AS numeric), 0) from db_bet WHERE "
        f"fee > 0 AND "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    return amount_formatter(value or 0)


def get_bets_amount_avg(currency, network_id):
    value = Base.session.execute(
        f"SELECT ROUND(CAST(coalesce(AVG(ABS(amount)), 0) AS numeric), 0) from db_bet WHERE "
        f"network_id={network_id} AND "
        f"currency = '{currency}';").scalar()
    return amount_formatter(value or 0)


@bets_router.post("/bets", status_code=200,
                  operation_id="getBets",
                  response_model=BetPage,
                  dependencies=[Depends(no_cache)])
async def get_bets(table_data: TableData, current_user: str = Depends(get_current_active_user)):
    bets = DbBet.query.filter(DbBet.network_id == table_data.networkId)

    if table_data.sortBy == "userAddress":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.user_address.desc())
        else:
            bets = bets.order_by(DbBet.user_address.asc())

    if table_data.sortBy == "asset":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.asset.desc())
        else:
            bets = bets.order_by(DbBet.asset.asc())

    if table_data.sortBy == "amount":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.amount.desc())
        else:
            bets = bets.order_by(DbBet.amount.asc())

    if table_data.sortBy == "paidAmount":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.paid_amount.desc())
        else:
            bets = bets.order_by(DbBet.paid_amount.asc())

    if table_data.sortBy == "currency":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.currency.desc())
        else:
            bets = bets.order_by(DbBet.currency.asc())

    if table_data.sortBy == "fee":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.fee.desc())
        else:
            bets = bets.order_by(DbBet.fee.asc())

    if table_data.sortBy == "created":
        if table_data.sortDesc:
            bets = bets.order_by(DbBet.created.desc())
        else:
            bets = bets.order_by(DbBet.created.asc())

    if table_data.searchData:
        if table_data.searchData["userAddress"]:
            bets = bets.filter(DbBet.user_address == table_data.searchData["userAddress"])
        if table_data.searchData["currency"]:
            bets = bets.filter(DbBet.currency == table_data.searchData["currency"].upper())
        if table_data.searchData["amount"]:
            bets = bets.filter(DbBet.amount == Web3.toWei(table_data.searchData["amount"], "ether"))

    bet_page = BetPage
    bet_page.bets = bets.offset((table_data.page - 1) * table_data.itemsPerPage).limit(table_data.itemsPerPage).all()
    bet_page.total = bets.count()
    return bet_page


@bets_router.get("/bet/{id}", status_code=200,
                 operation_id="getBet",
                 response_model=Bet,
                 dependencies=[Depends(no_cache)])
async def get_bet(id: str, current_user: str = Depends(get_current_active_user)):
    user = DbBet.where(id=id).first()
    return user


@bets_router.get("/win_loss/{network_id}", status_code=200,
                 operation_id="getWinLoss",
                 response_model=WinLoss,
                 dependencies=[Depends(no_cache)])
async def get_win_loss(network_id: int, current_user: str = Depends(get_current_active_user)):
    W3 = Web3(WebsocketProvider(settings.NETWORKS[network_id].NODE_URL))
    eth_contract_data = settings.NETWORKS[network_id].ETH_CONTRACT
    usdt_contract_data = settings.NETWORKS[network_id].USDT_CONTRACT
    with open(settings.NETWORKS[network_id].ERC20_CONTRACT['abi'], 'r') as f:
        erc20_abi = json.dumps(json.loads(f.read()))
    erc_20_contract = W3.eth.contract(Web3.toChecksumAddress(settings.NETWORKS[network_id].ERC20_CONTRACT.ADDRESS),
                                      abi=json.loads(erc20_abi))

    eth_balance = W3.eth.getBalance(eth_contract_data.ADDRESS)
    # return network_id
    usdt_balance = erc_20_contract.functions.balanceOf(usdt_contract_data.ADDRESS).call() * 10 ** 12
    # usdt_balance = erc_20_contract.functions.balanceOf("0xAB82007271685cc960a4Cc4417d716205C1779CE").call() * 10 ** 12
    win_loss = WinLoss
    win_loss.network_id = network_id
    win_loss.win_count = get_bets_count(result=BetResult.WIN, network_id=network_id, currency=Currency.ETH)
    win_loss.loss_count = get_bets_count(result=BetResult.LOSS, network_id=network_id, currency=Currency.ETH)
    win_loss.draw_count = get_bets_count(result=BetResult.DRAW, network_id=network_id, currency=Currency.ETH)
    win_loss.total_count = get_bets_count(network_id=network_id, currency=Currency.ETH)
    win_loss.win_count_usdt = get_bets_count(result=BetResult.WIN, network_id=network_id, currency=Currency.USDT)
    win_loss.loss_count_usdt = get_bets_count(result=BetResult.LOSS, network_id=network_id, currency=Currency.USDT)
    win_loss.draw_count_usdt = get_bets_count(result=BetResult.DRAW, network_id=network_id, currency=Currency.USDT)
    win_loss.total_count_usdt = get_bets_count(network_id=network_id, currency=Currency.USDT)
    win_loss.avg_eth = f"{get_bets_amount_avg(Currency.ETH, network_id):>10} ETH"
    win_loss.avg_usdt = f"{get_bets_amount_avg(Currency.USDT, network_id):>10} USDT"
    win_loss.win_eth = f"{get_bets_amount_sum(Currency.ETH, BetResult.WIN, network_id):>10} ETH"
    win_loss.win_usdt = f"{get_bets_amount_sum(Currency.USDT, BetResult.WIN, network_id):>10} USDT"
    win_loss.loss_eth = f"{get_bets_amount_sum(Currency.ETH, BetResult.LOSS, network_id):>10} ETH"
    win_loss.loss_usdt = f"{get_bets_amount_sum(Currency.USDT, BetResult.LOSS, network_id):>10} USDT"
    win_loss.user_total_deposit_eth = f"{get_users_sum(Currency.ETH, 'Deposited', network_id):>10} ETH"
    win_loss.user_total_deposit_usdt = f"{get_users_sum(Currency.USDT, 'Deposited', network_id):>10} USDT"
    win_loss.user_total_withdraw_eth = f"{get_users_sum(Currency.ETH, 'Withdraw', network_id):>10} ETH"
    win_loss.user_total_withdraw_usdt = f"{get_users_sum(Currency.USDT, 'Withdraw', network_id):>10} USDT"
    win_loss.loss_usdt = f"{get_bets_amount_sum(Currency.USDT, BetResult.LOSS, network_id):>10} USDT"
    win_loss.eth_contract_balance = amount_formatter(eth_balance)
    win_loss.usdt_contract_balance = amount_formatter(usdt_balance)
    win_loss.avg_fee_eth = f"{get_bets_fee_avg(Currency.ETH, network_id):>10} ETH"
    win_loss.avg_fee_usdt = f"{get_bets_fee_avg(Currency.USDT, network_id):>10} USDT"
    win_loss.total_fee_eth = f"{get_bets_fee_sum(Currency.ETH, network_id):>10} ETH"
    win_loss.total_fee_usdt = f"{get_bets_fee_sum(Currency.USDT, network_id):>10} USDT"
    win_loss.total_eth_24 = f"{get_bets_amount_sum_24(Currency.ETH, network_id):>10} ETH"
    win_loss.total_usdt_24 = f"{get_bets_amount_sum_24(Currency.USDT, network_id):>10} USDT"
    win_loss.total_eth_week = f"{get_bets_amount_sum_week(Currency.ETH, network_id):>10} ETH"
    win_loss.total_usdt_week = f"{get_bets_amount_sum_week(Currency.USDT, network_id):>10} USDT"
    win_loss.total_eth_month = f"{get_bets_amount_sum_month(Currency.ETH, 1, network_id):>10} ETH"
    win_loss.total_usdt_month = f"{get_bets_amount_sum_month(Currency.USDT, 1, network_id):>10} USDT"
    win_loss.total_eth_3month = f"{get_bets_amount_sum_month(Currency.ETH, 3, network_id):>10} ETH"
    win_loss.total_usdt_3month = f"{get_bets_amount_sum_month(Currency.USDT, 3, network_id):>10} USDT"
    win_loss.total_eth_6month = f"{get_bets_amount_sum_month(Currency.ETH, 6, network_id):>10} ETH"
    win_loss.total_usdt_6month = f"{get_bets_amount_sum_month(Currency.USDT, 6, network_id):>10} USDT"

    return win_loss


@bets_router.put("/bet/{bet_id}", status_code=200,
                 operation_id="updateBet",
                 response_model=Bet,
                 dependencies=[Depends(no_cache)])
async def update_bet(bet_id: int, bet_input: BetEdit, current_user: str = Depends(get_current_active_user)):
    bet = DbBet.where(id=bet_id).first()

    if not bet:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Bet not found")
    bet.update(amount=bet_input.amount, paid_amount=bet_input.paid_amount, fee=bet_input.fee,
               result=BetResult[bet_input.result])

    DbBet.session.commit()
    return bet
