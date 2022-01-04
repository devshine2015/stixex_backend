from datetime import datetime, timedelta, timezone
from decimal import Decimal

from dynaconf import settings
from fastapi_sqlalchemy import DBSessionMiddleware, db
from loguru import logger
from markupsafe import Markup
from sqlalchemy import *
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy_mixins import AllFeaturesMixin
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request

from app.common.api_models import AssetCandle
from app.common.enums import Asset, Currency, BetChoice, BetStatus, BetResult, WithdrawStatus, TimeFrame
from app.common.utils import camel_to_snake, emit, amount_formatter


@as_declarative()
class Base(AllFeaturesMixin):
    __abstract__ = True

    @declared_attr
    def __tablename__(self):
        return camel_to_snake(self.__name__)


class DBMiddleware(DBSessionMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # noinspection PyCallingNonCallable
        with db(commit_on_exit=self.commit_on_exit):
            Base.set_session(db.session)
            response = await call_next(request)
        return response


class DbUser(Base):
    eth_balance = Column(Numeric, default=0)
    usdt_balance = Column(Numeric, default=0)
    address = Column(String)

    network_id = Column(Integer)
    created = Column(DateTime, default=datetime.utcnow)
    activated = Column(DateTime, default=None)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'network_id'),
        {},
    )

    def __repr__(self):
        return self.address

    def emit(self, event, data):
        logger.debug(f'{event} emited')
        emit(f"{self.address}-{self.network_id}", event, data)
        emit("admins-room", event, data)

    @property
    def usdt_bets_count(self):
        return DbBet.where(user=self, currency=Currency.USDT).count()

    @property
    def eth_bets_count(self):
        return DbBet.where(user=self, currency=Currency.ETH).count()

    @property
    def eth_withdraw_requested(self):
        return DbWithdraw.where(user_address=self.address,
                                network_id=self.network_id,
                                currency=Currency.ETH,
                                status=WithdrawStatus.PENDING).first() is not None

    @property
    def last_deposited_currency(self):
        last_event: DbChainEvent = DbChainEvent.where(user_address=self.address,
                                                      network_id=self.network_id).order_by(
            DbChainEvent.created.desc()).first()
        last_bet: DbBet = DbBet.where(user_address=self.address,
                                      network_id=self.network_id).order_by(DbBet.created.desc()).first()
        last_withdraw_request: DbWithdraw = DbWithdraw.where(user_address=self.address,
                                                             network_id=self.network_id).order_by(
            DbWithdraw.created.desc()).first()
        items = list(filter(lambda x: x, [last_bet, last_withdraw_request, last_event]))
        if items:
            return max(items, key=lambda x: x.created).currency
        else:
            return Currency.ETH

    @property
    def eth_withdraw_request(self):
        return DbWithdraw.where(user_address=self.address,
                                network_id=self.network_id,
                                currency=Currency.ETH).order_by(DbWithdraw.created.desc()).first()

    @property
    def usdt_withdraw_request(self):
        return DbWithdraw.where(user_address=self.address,
                                network_id=self.network_id,
                                currency=Currency.USDT).order_by(DbWithdraw.created.desc()).first()

    @property
    def has_pending_bets(self):
        return DbBet.where(user_address=self.address,
                           network_id=self.network_id,
                           status=BetStatus.PROCESSING).first() is not None

    @property
    def usdt_withdraw_requested(self):
        return DbWithdraw.where(user_address=self.address,
                                network_id=self.network_id,
                                currency=Currency.USDT,
                                status=WithdrawStatus.PENDING).first() is not None

    @property
    def win_loss_ratio(self):
        def get_bets_count(**kwargs):
            return DbBet.where(user=self, **kwargs).count()

        def get_bets_amount_sum(currency, result):
            value = Base.session.execute(
                f"SELECT ROUND(CAST(coalesce(SUM(ABS(amount)), 0) AS numeric), 0) from db_bet WHERE "
                f"result='{result}' AND "
                f"network_id={self.network_id} AND "
                f"user_address = '{self.address}' AND "
                f"currency = '{currency}';").scalar()
            return amount_formatter(value or 0)

        def get_bets_win_amount(currency):
            value = Base.session.execute(
                f"SELECT ROUND(CAST(coalesce(SUM(ABS(paid_amount - amount)), 0) AS numeric), 0) from db_bet WHERE "
                f"result='{BetResult.WIN}' AND "
                f"network_id={self.network_id} AND "
                f"user_address = '{self.address}' AND "
                f"currency = '{currency}';").scalar()
            return amount_formatter(value or 0)

        def get_bets_amount_avg(currency):
            value = Base.session.execute(
                f"SELECT ROUND(CAST(coalesce(AVG(amount), 0) AS numeric), 0) from db_bet WHERE "
                f"network_id={self.network_id} AND "
                f"user_address = '{self.address}' AND "
                f"currency = '{currency}';").scalar()
            return amount_formatter(value or 0)

        return Markup(f"<pre>"
                      f"Win ETH: {get_bets_count(result=BetResult.WIN,currency=Currency.ETH)}\n"
                      f"Loss ETH: {get_bets_count(result=BetResult.LOSS,currency=Currency.ETH)}\n"
                      f"Draw ETH: {get_bets_count(result=BetResult.DRAW,currency=Currency.ETH)}\n"
                      f"Total ETH: {get_bets_count(currency=Currency.ETH)}\n\n"
                      f"Win USDT: {get_bets_count(result=BetResult.WIN,currency=Currency.USDT)}\n"
                      f"Loss USDT: {get_bets_count(result=BetResult.LOSS,currency=Currency.USDT)}\n"
                      f"Draw USDT: {get_bets_count(result=BetResult.DRAW,currency=Currency.USDT)}\n"
                      f"Total USDT: {get_bets_count(currency=Currency.USDT)}\n\n"
                      f"Win:  {get_bets_win_amount(Currency.ETH):>10} ETH, "
                      f"{get_bets_win_amount(Currency.USDT):>10} USDT\n"
                      f"Loss: {get_bets_amount_sum(Currency.ETH, BetResult.LOSS):>10} ETH, "
                      f"{get_bets_amount_sum(Currency.USDT, BetResult.LOSS):>10} USDT\n\n"
                      f"---- \n\n"
                      f"Average Bet ETH : {get_bets_amount_avg(Currency.ETH):>10} ETH\n\n"
                      f"Average Bet USDT:{get_bets_amount_avg(Currency.USDT):>10} USDT\n\n"
                      f"</pre>")

    @property
    def deposits_withdraws(self):
        def get_amount_sum(currency, event):
            value = Base.session.execute(
                f"SELECT ROUND(CAST(coalesce(SUM(amount), 0) AS numeric), 0) from db_chain_event WHERE "
                f"name='{event}' AND "
                f"network_id={self.network_id} AND "
                f"user_address = '{self.address}' AND "
                f"currency = '{currency}';").scalar()
            if value:
                if currency == Currency.USDT:
                    value *= 10 ** 12
            else:
                value = 0
            return amount_formatter(value)

        def get_count(currency, event):
            return DbChainEvent.where(name=event, network_id=self.network_id, user_address=self.address,
                                      currency=currency).count()

        return Markup(f""
                      f"<pre>"
                      f"Deposits ETH: {get_count(Currency.ETH, 'Deposited')} Deposits USDT: {get_count(Currency.USDT, 'Deposited')}\n"
                      f"Withdraws ETH: {get_count(Currency.ETH, 'Withdraw')} Withdraws USDT: {get_count(Currency.USDT, 'Withdraw')}\n"

                      f"Deposits:  {get_amount_sum(Currency.ETH, 'Deposited'):>10} ETH, "
                      f"{get_amount_sum(Currency.USDT, 'Deposited'):>10} USDT\n"
                      f"Withdraws: "
                      f"{get_amount_sum(Currency.ETH, 'Withdraw'):>10} ETH, "
                      f"{get_amount_sum(Currency.USDT, 'Withdraw'):>10} USDT"
                      f"</pre>")


class DbBet(Base):
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    amount = Column(Numeric)
    paid_amount = Column(Numeric, default=0)
    currency = Column(Enum(Currency, create_constraint=False, native_enum=False))
    asset = Column(Enum(Asset, create_constraint=False, native_enum=False))
    choice = Column(Enum(BetChoice, create_constraint=False, native_enum=False))
    result = Column(Enum(BetResult, create_constraint=False, native_enum=False))
    fee = Column(Float)
    fee_amount = Column(Numeric)
    payout = Column(Float)
    interval_start = Column(DateTime)
    time_frame = Column(Enum(TimeFrame, create_constraint=False, native_enum=False))
    status = Column(Enum(BetStatus, create_constraint=False, native_enum=False))
    user_address = Column(String)
    user = relationship('DbUser')

    network_id = Column(Integer)
    created = Column(DateTime, default=datetime.utcnow)

    result_candle = Column(JSON)

    __table_args__ = (ForeignKeyConstraint([user_address, network_id],
                                           [DbUser.address, DbUser.network_id]),
                      {})

    @property
    def full_amount(self):
        return Decimal(self.amount + self.fee_amount)

    @property
    def payout_amount(self):
        value = int(self.amount) * self.payout
        multiplier = 10 ** 14
        return Decimal(value // multiplier * multiplier)

    @property
    def interval_end(self):
        return self.interval_start + timedelta(minutes=self.time_frame)

    def process_payout(self):
        self.status = BetStatus.COMPLETED

        if self.result == BetResult.DRAW:
            if self.currency == Currency.ETH:
                self.user.eth_balance += self.amount
            if self.currency == Currency.USDT:
                self.user.usdt_balance += self.amount
            self.paid_amount = self.amount

        if self.result == BetResult.LOSS:
            self.paid_amount = 0

        if self.result == BetResult.WIN:
            if self.currency == Currency.ETH:
                self.user.eth_balance += self.payout_amount
            if self.currency == Currency.USDT:
                self.user.usdt_balance += self.payout_amount
            self.paid_amount = self.payout_amount

    def process_result(self, candle: AssetCandle):
        self.result_candle = candle.json()
        if candle.open == candle.close:  # DRAW
            self.result = BetResult.DRAW
        if candle.open < candle.close:  # GREEN
            self.result = BetResult.WIN if self.choice == BetChoice.GREEN else BetResult.LOSS
        if candle.open > candle.close:  # RED
            self.result = BetResult.WIN if self.choice == BetChoice.RED else BetResult.LOSS
        self.process_payout()


class DbChainEvent(Base):
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    transaction_hash = Column(String)
    contract_address = Column(String)
    network_id = Column(Integer)
    name = Column(String)
    block = Column(String)
    user_address = Column(String)
    currency = Column(Enum(Currency, create_constraint=False, native_enum=False))
    user = relationship('DbUser')
    amount = Column(Numeric)
    data = Column(JSON)
    created = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (ForeignKeyConstraint([user_address, network_id],
                                           [DbUser.address, DbUser.network_id]),
                      {})


class DbWithdraw(Base):
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    amount = Column(Numeric, default=0)
    currency = Column(Enum(Currency, create_constraint=False, native_enum=False))
    status = Column(Enum(WithdrawStatus, create_constraint=False, native_enum=False), default=WithdrawStatus.PENDING)
    withdraw_request_signature = Column(String)
    user_address = Column(String)
    user = relationship('DbUser')
    network_id = Column(Integer)
    session_id = Column(Integer)
    reject_message = Column(String)
    created = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (ForeignKeyConstraint([user_address, network_id],
                                           [DbUser.address, DbUser.network_id]),
                      {})

    @property
    def signing_args(self):
        return [self.user_address, str(self.amount)]

    def approve(self, signature):
        self.withdraw_request_signature = signature
        self.status = WithdrawStatus.APPROVED

    def reject(self, reject_message):
        if self.currency == Currency.ETH:
            self.user.eth_balance += self.amount
        if self.currency == Currency.USDT:
            self.user.usdt_balance += self.amount
        self.withdraw_request_signature = None
        self.reject_message = reject_message
        self.status = WithdrawStatus.REJECTED

    def cancel(self):
        if self.currency == Currency.ETH:
            self.user.eth_balance += self.amount
        if self.currency == Currency.USDT:
            self.user.usdt_balance += self.amount
        self.status = WithdrawStatus.CANCELED


class AppSettings(Base):
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    bet_fee = Column(Float, default=settings.DEFAULT_FEE)
    bet_payout = Column(Float, default=settings.DEFAULT_PAYOUT)
    min_deposit_amount = Column(Numeric, default=settings.MIN_DEPOSIT_AMOUNT)
    min_deposit_amount_usdt = Column(Numeric, default=settings.MIN_DEPOSIT_AMOUNT_USDT)
    maintenance = Column(Boolean, default=False)

    @property
    def instance(self):
        return self.first()


class DbLog(Base):
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    log_description = Column(String)
    network_id = Column(Integer)
    created = Column(DateTime, default=datetime.utcnow)

class DbReferral(Base):
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    user_address = Column(String)
    friend_address = Column(String)
    network_id = Column(Integer)
    user = relationship('DbUser')
    currency = Column(Enum(Currency, create_constraint=False, native_enum=False))
    earnings = Column(Float)
    created = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (ForeignKeyConstraint([user_address, network_id],
                                           [DbUser.address, DbUser.network_id]),
                      {})