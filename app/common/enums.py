import enum


class Asset(str, enum.Enum):
    ETH_USDT = 'ETHUSDT'
    BTC_USDT = 'BTCUSDT'


class Currency(str, enum.Enum):
    ETH = 'ETH'
    USDT = 'USDT'


class BetChoice(str, enum.Enum):
    GREEN = 'GREEN'
    RED = 'RED'


class BetStatus(str, enum.Enum):
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'


class BetResult(str, enum.Enum):
    WIN = 'WIN'
    DRAW = 'DRAW'
    LOSS = 'LOSS'


class WithdrawStatus(str, enum.Enum):
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    PENDING = 'PENDING'
    CANCELED = 'CANCELED'
    COMPLETED = 'COMPLETED'


class TimeFrame(enum.IntEnum):
    ONE_MIN = 1
    FIVE_MIN = 5
    FIFTEEN_MIN = 15


class SocketEvents(str, enum.Enum):
    CHAIN_EVENT_CREATED = 'CHAIN_EVENT_CREATED'
    WITHDRAW_STATE_CHANGED = 'WITHDRAW_STATE_CHANGED'
    USER_STATE_CHANGED = 'USER_STATE_CHANGED'
    WITHDRAW_CREATED = 'WITHDRAW_CREATED'
    BET_CREATED = 'BET_CREATED'
    BET_STATE_CHANGED = 'BET_STATE_CHANGED'
