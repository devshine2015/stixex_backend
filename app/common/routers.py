import decimal
import json
import math
from datetime import timezone, datetime
from http import HTTPStatus
import redis
import requests
from dynaconf import settings
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi_sqlalchemy import db
from starlette.responses import HTMLResponse
from web3 import Web3, WebsocketProvider

from app.common.api_models import *
from app.common.db_models import DbUser, DbBet, DbWithdraw, AppSettings
from app.common.dependencies import SignedRequestOperations, ChainEventOperations, no_cache
from app.common.enums import Asset, TimeFrame, WithdrawStatus, SocketEvents
from app.common.enums import Currency
from app.common.utils import get_nearest_interval_start, get_history_by_asset, redis_client, round_integer

default_router = APIRouter()
event_router = APIRouter()
misc_router = APIRouter()


@default_router.post("/create_bet", status_code=200, operation_id="createBet", response_model=Bet)
async def create_bet(amount: int,
                     asset: Asset,
                     choice: BetChoice,
                     currency: Currency,
                     # interval_start: datetime,
                     time_frame: TimeFrame,
                     network_id: int,
                     user=Depends(SignedRequestOperations.get_signer_from_signature)):
    if AppSettings().instance.maintenance:
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE, "Maintenance")
    interval_start = get_nearest_interval_start(time_frame)
    if not user:
        raise HTTPException(HTTPStatus.NOT_FOUND, "User not found")
    if interval_start < get_nearest_interval_start(time_frame):
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Interval start passed")
    if amount <= 0:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Invalid amount")
    amount = round_integer(amount, 5)
    fee_amount = amount * AppSettings().instance.bet_fee / 100
    balance = user.eth_balance if currency == Currency.ETH else user.usdt_balance
    if balance < amount:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Not enough balance")
    if balance - decimal.Decimal(amount) - decimal.Decimal(fee_amount) < 10 ** 13 * 2:
        fee_amount = balance - amount
    else:
        if fee_amount < 10 ** 13 and AppSettings().instance.bet_fee != 0:
            fee_amount = 10 ** 13
        else:
            fee_amount = math.ceil(fee_amount / 10 ** 13) * 10 ** 13
    has_bet_on_the_same_candle = DbBet.where(
        interval_start=interval_start,
        time_frame=time_frame,
        network_id=network_id,
        user_address=user.address
    ).first() is not None

    if has_bet_on_the_same_candle:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "User has a bet on the same candle")

    bet = DbBet.create(amount=amount,
                       asset=asset,
                       choice=choice,
                       currency=currency,
                       interval_start=interval_start,
                       time_frame=time_frame,
                       network_id=network_id,
                       user_address=user.address,
                       fee=AppSettings().instance.bet_fee / 100,
                       fee_amount=fee_amount,
                       payout=1 + AppSettings().instance.bet_payout / 100,
                       status=BetStatus.PROCESSING)
    if currency == Currency.ETH:
        user.eth_balance -= bet.full_amount
        if user.eth_balance < 0:
            db.session.rollback()
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Insufficient ETH balance")
    if currency == Currency.USDT:
        user.usdt_balance -= bet.full_amount
        if user.usdt_balance < 0:
            db.session.rollback()
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Insufficient USDT balance")
    user.activated = datetime.utcnow()
    db.session.commit()
    print(bet)
    user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(user))
    user.emit(SocketEvents.BET_CREATED, Bet.from_orm(bet))
    return bet


@default_router.post("/create_withdraw_request",
                     status_code=200,
                     operation_id="createWithdrawRequest")
async def create_withdraw_request(network_id: int, currency: Currency,
                                  user=Depends(SignedRequestOperations.get_signer_from_signature)):
    if AppSettings().instance.maintenance:
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE, "Maintenance")
    if not user:
        raise HTTPException(HTTPStatus.NOT_FOUND, "User not found")
    # TODO Move amount to args after contract change
    amount = user.eth_balance if currency == Currency.ETH else user.usdt_balance
    if amount < 10 ** 14:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Min withdraw amount 0.0001")
    if currency == Currency.ETH and user.eth_balance < amount:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Insufficient ETH balance")
    if currency == Currency.USDT and user.usdt_balance < amount:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Insufficient USDT balance")
    if DbWithdraw.where(currency=currency, user_address=user.address, network_id=user.network_id,
                        status=WithdrawStatus.PENDING).first():
        raise HTTPException(HTTPStatus.BAD_REQUEST, "You already have pending request for this currency")

    W3 = Web3(WebsocketProvider(settings.NETWORKS[network_id].NODE_URL))
    if currency == Currency.ETH:
        contract_data = settings.NETWORKS[network_id].ETH_CONTRACT
    else:
        contract_data = settings.NETWORKS[network_id].USDT_CONTRACT
    with open(contract_data['abi'], 'r') as f:
        contract = W3.eth.contract(contract_data.ADDRESS, abi=json.loads(f.read()))
    session_id = contract.functions.getUserActiveSessionId(user.address).call()

    withdraw = DbWithdraw.create(amount=amount, session_id=session_id, currency=currency, user_address=user.address,
                                 network_id=user.network_id)
    if currency == Currency.ETH:
        user.eth_balance -= amount
    if currency == Currency.USDT:
        user.usdt_balance -= amount
    db.session.commit()
    user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(user))
    user.emit(SocketEvents.WITHDRAW_CREATED, Withdraw.from_orm(withdraw))


@default_router.post("/cancel_withdraw_request",
                     status_code=200,
                     operation_id="cancelWithdrawRequest")
async def cancel_withdraw_request(withdraw_id: int, network_id: int,
                                  user=Depends(SignedRequestOperations.get_signer_from_signature)):
    if AppSettings().instance.maintenance:
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE, "Maintenance")
    if not user:
        raise HTTPException(HTTPStatus.NOT_FOUND, "User not found")
    withdraw = DbWithdraw.where(id=withdraw_id).first()
    if not withdraw:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Withdraw with this id not found")
    if withdraw.status != WithdrawStatus.PENDING:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Withdraw already processed")
    withdraw.cancel()
    db.session.commit()
    user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(user))
    user.emit(SocketEvents.WITHDRAW_STATE_CHANGED, Withdraw.from_orm(withdraw))


@default_router.get("/bets_history",
                    status_code=200,
                    operation_id="getBetsHistory",
                    response_model=List[Bet],
                    dependencies=[Depends(no_cache)])
async def get_bets_history(network_id: int, user_address: str, currency: Currency = None, limit: int = 10,
                           offset: int = 0):
    query = DbBet.where(network_id=network_id, user_address=user_address)
    if currency:
        query = query.filter(DbBet.currency == currency)
    return query.order_by(
        DbBet.created.desc()).offset(offset).limit(limit).all()


@default_router.get("/user_information", status_code=200, operation_id="getUserInformation", response_model=User,
                    dependencies=[Depends(no_cache)])
async def get_user_information(network_id: int, user_address: str):
    user = DbUser.where(address=user_address, network_id=network_id).first()
    if not user:
        raise HTTPException(HTTPStatus.NOT_FOUND, "User not found")
    return user


@default_router.get("/withdraw_history", status_code=200, operation_id="getWithdrawHistory",
                    response_model=List[Withdraw], dependencies=[Depends(no_cache)])
async def get_withdraw_history(network_id: int, user_address: str,
                               currency: Currency = None,
                               offset: int = 0, limit: int = 10):
    query = DbWithdraw.where(user_address=user_address, network_id=network_id)
    if currency:
        query = query.filter(DbWithdraw.currency == currency)
    return query.order_by(
        DbWithdraw.created.desc()).offset(offset).limit(limit).all()


@event_router.post("/deposited", status_code=200, operation_id="eventDeposited",
                   dependencies=[Depends(ChainEventOperations.create_event_db_record)])
async def event_deposited(account: str, amount: int, block: int, network_id: int, address: str, currency: Currency):
    user = DbUser.where(address=account, network_id=network_id).first()
    if currency == Currency.ETH:
        user.eth_balance += amount
    if currency == currency.USDT:
        user.usdt_balance += amount * 10 ** 12  # szabo
    db.session.commit()
    deposited_data = User.from_orm(user)
    deposited_data.not_for_user = True
    user.emit(SocketEvents.USER_STATE_CHANGED, deposited_data)
    return {"success": True}


@event_router.post("/withdraw", status_code=200, operation_id="eventWithdraw",
                   dependencies=[Depends(ChainEventOperations.create_event_db_record)])
async def event_withdraw(account: str, amount: int, network_id: int, address: str):
    user = DbUser.where(address=account, network_id=network_id).first()
    if user:
        currency = None
        if address == settings.NETWORKS[network_id].ETH_CONTRACT['address']:
            currency = Currency.ETH
        if address == settings.NETWORKS[network_id].USDT_CONTRACT['address']:
            currency = Currency.USDT
        if currency == Currency.USDT:
            amount *= 10 ** 12

        withdraw = DbWithdraw.where(user_address=account, network_id=network_id,amount=amount,
                                    currency=currency,
                                    status=WithdrawStatus.APPROVED).first()
        if withdraw:
            withdraw.status = WithdrawStatus.COMPLETED
            db.session.commit()
            user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(withdraw.user))
            user.emit(SocketEvents.WITHDRAW_STATE_CHANGED, Withdraw.from_orm(withdraw))

@event_router.post("/join_referral", status_code=200, operation_id="joinReferral", dependencies=[Depends(no_cache)])
async def join_referral(referral_code: str, user_address: str, network_id: int):
    # check if the user is new user
    old_user = DbUser.where(address=user_address, network_id=network_id).first()
    if not old_user:
        user = DbUser.where(address=referral_code, network_id=network_id).first()
        if not user:
            return {"success": False, "message": "The referral code is invalid!"}
        else:
            new_user = DbUser.create(address=user_address, network_id=network_id)
            DbUser.session.commit()
        return {"success": True,  "is_new_user": True, "message": "You are joined successfully!"}
    return {"success": False, "message": "You are not new user.", "is_new_user": False}

@event_router.post("/signin", status_code=200, operation_id="signInUser", dependencies=[Depends(no_cache)])
async def signin_user(user_address: str, network_id: int):
    user = DbUser.where(address=user_address, network_id=network_id).first()
    if not user:
        return {"success": False, "message": "You are a new user! You should join with user token first.", "is_new_user": True}
    return {"success": True,  "is_new_user": False}


@misc_router.get("/all_prices", status_code=200, operation_id="allPrices", response_model=AllPrices,
                 dependencies=[Depends(no_cache)])
async def all_prices():
    cached_value = redis_client.get('tickers')
    if not cached_value:
        cached_value = AllPrices(
            BTC=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT').json()['price'],
            ETH=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT').json()['price']
        ).json()
        redis_client.set('tickers', cached_value)
        redis_client.expire('tickers', 3)
    return json.loads(cached_value)


@misc_router.get("/asset_candle", status_code=200, operation_id="getAssetCandle",
                 response_model=AssetCandle, dependencies=[Depends(no_cache)])
async def get_asset_candle(time_frame: TimeFrame, asset: Asset, time_start: Optional[datetime] = None,
                           time_end: Optional[datetime] = None):
    return get_history_by_asset(time_frame, asset, time_start, time_end)


@misc_router.get("/server_time", status_code=200, operation_id="getServerTime", response_model=ServerTime,
                 dependencies=[Depends(no_cache)])
async def get_server_time():
    return ServerTime(
        timestamp=int(datetime.now(timezone.utc).timestamp()),
        iso=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )


@misc_router.get("/server_params", status_code=200, operation_id="getSystemParams", response_model=SystemParams,
                 dependencies=[Depends(no_cache)])
async def get_server_params():
    app_settings = AppSettings().instance
    return SystemParams(
        fee=app_settings.bet_fee / 100,
        payout=app_settings.bet_payout / 100 + 1,
        maintenance=app_settings.maintenance
    )


@misc_router.get("/nearest_interval_start", status_code=200, operation_id="getNearestIntervalStart",
                 response_model=ServerTime, dependencies=[Depends(no_cache)])
async def get_nearest_interval_start_(timeframe: TimeFrame):
    i_s = get_nearest_interval_start(timeframe)
    return ServerTime(timestamp=int(i_s.timestamp()), iso=i_s.replace(microsecond=0).isoformat())


@misc_router.get("/signature", include_in_schema=True)
async def get_signature(args: List[str] = Query(None)):
    if not args:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Cant sign empty string")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="/static/request_signing.js"></script>
</head>
<body>
    <h4 style="text-align: center; margin-top: 100px" id="message">{'|'.join(args)}</pre>
    <h3 style="text-align: center" id="signature"></h3>
</body>
</html>
"""
    return HTMLResponse(html)
