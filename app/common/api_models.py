from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional

from pydantic.types import Json

from app.common.enums import Asset, Currency, BetChoice, BetStatus, TimeFrame, WithdrawStatus
from app.common.utils import snake_to_camel


class BaseApiModel(BaseModel):
    class Config:
        allow_population_by_alias = True
        orm_mode = True
        alias_generator = snake_to_camel


class Withdraw(BaseApiModel):
    id: int
    user_address: str
    amount: int
    currency: Currency
    status: WithdrawStatus
    network_id: int
    session_id: int
    reject_message: Optional[str]
    withdraw_request_signature: Optional[str]
    created: datetime


class WithdrawPage(BaseApiModel):
    total: int
    withdraws: List[Withdraw]


class WithdrawActionResult(BaseApiModel):
    id: int
    user_address: str
    success: bool = False
    message: Optional[str]


class WithdrawApproveData(BaseApiModel):
    id: int
    user_address: str
    signature: str


class WithdrawRejectData(BaseApiModel):
    id: int
    user_address: str
    reject_message: str


class User(BaseApiModel):
    address: str
    network_id: int
    eth_balance: int
    usdt_balance: int
    eth_balance_fee:int
    usdt_balance_fee:int
    created: datetime
    eth_bets_count: int
    usdt_bets_count: int
    eth_withdraw_requested: bool
    usdt_withdraw_requested: bool
    has_pending_bets: bool
    last_deposited_currency: Currency
    eth_withdraw_request: Optional[Withdraw]
    usdt_withdraw_request: Optional[Withdraw]
    win_loss_ratio: Optional[str]
    deposits_withdraws: Optional[str]
    not_for_user: bool = False
    referral_point:int
   


class UserEdit(BaseApiModel):
    network_id: int
    eth_balance: int
    usdt_balance: int


class Bet(BaseApiModel):
    id: int
    amount: int
    asset: Asset
    choice: BetChoice
    currency: Currency
    interval_start: datetime
    time_frame: TimeFrame
    network_id: int
    paid_amount: Optional[int]
    fee: Optional[float]
    fee_amount: Optional[int]
    payout: Optional[float]
    status: BetStatus
    user_address: str
    created: datetime
    result: Optional[str] = None
    result_candle: Json


class BetEdit(BaseApiModel):
    amount: int
    paid_amount: int
    fee: float
    result: str


class UserPage(BaseApiModel):
    total: int
    users: List[User]


class BetPage(BaseApiModel):
    total: int
    bets: List[Bet]


class ServerTime(BaseApiModel):
    timestamp: int
    iso: str


class SystemParams(BaseApiModel):
    fee: float
    payout: float
    maintenance: bool


class AllPrices(BaseApiModel):
    ETH: float
    BTC: float


class AssetCandle(BaseApiModel):
    start: datetime
    end: datetime
    time_frame: TimeFrame
    open: float
    close: float


class ApiAppSettingsModel(BaseApiModel):
    bet_fee: float
    bet_payout: float
    maintenance: bool
