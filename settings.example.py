# Api
REDIS_URL = "redis://"
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True
DATABASE_URL = "postgresql+psycopg2://postgres:@localhost:5432/stixex"
POST_PROCESS_SCHEMA = True
USE_SENTRY = False
SENTRY_KEY = "https://@sentry.io/"
CORS_ORIGINS = ["*"]
STATIC_PATH = "./static"
DEFAULT_FEE = 3
DEFAULT_PAYOUT = 200
MIN_DEPOSIT_AMOUNT = 0.01
MIN_DEPOSIT_AMOUNT_USDT = 2

# Admin
ADMIN_HOST = "0.0.0.0"
ADMIN_PORT = 80
AUTH_LOGIN = 'admin'
AUTH_PASSWORD = '8vVq34uq57NeG'
SECRET_KEY = 'Hs7osKsw32lSj27sJ702J23m0'

# Listener
DELAY = 10

API_EVENT_URL = "http://localhost:8000/"

NETWORKS = {
    4: {
        "NODE_URL": "wss://rinkeby.infura.io/ws/v3/ecd39e761b194b9faf18bc4338b50517",
        "ETH_CONTRACT": {
            "abi": "../contracts/StixexETH.json",
            "address": "0x10b4Fa9845B302d6E8de08fC075616ccEf2FB424",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "USDT_CONTRACT": {
            "abi": "../contracts/StixexETH.json",
            "address": "0xBEFEE7C0c2ED207F724F2B597380F86490c82ca8",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        'ADMIN': '0xdD82B8F6194681d641CA3Cba6a83E56A3cE66A4f'
    }
}
