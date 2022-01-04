# Api
REDIS_URL = "redis://"
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/stixex"
POST_PROCESS_SCHEMA = True
USE_SENTRY = True
SENTRY_KEY = "https://8ec16c5a70f94b368f639a875582aa3d@o762318.ingest.sentry.io/5793408"
CORS_ORIGINS = ["*"]
STATIC_PATH = "/home/ubuntu/stixex_backend1/app/static"
DEFAULT_FEE = 0.03
DEFAULT_PAYOUT = 2
MIN_DEPOSIT_AMOUNT=0.01
MIN_DEPOSIT_AMOUNT_USDT=2
# cron-job

# Admin
ADMIN_HOST = "http://65.108.54.212:8001"
ADMIN_PORT = 443
AUTH_LOGIN = 'stixex'
AUTH_PASSWORD = 'palanga'
SECRET_KEY = 'Hs7osKsw32lSj27sJ702J23m0'
ENABLED_NETWORK_NUMBERS = [1, 3, 4]
# Listener
DELAY = 10

API_EVENT_URL = "http://65.108.54.212:8000"

NETWORKS = {
    1: {
        "NODE_URL": "wss://mainnet.infura.io/ws/v3/5989bfec84544b4ba8ccca58cf9e9395",
        "ETH_CONTRACT": {
            "abi": "./contracts/StixexETH.json",
            "address": "0x0eDa54F63B2c1ea17B6eda828E7eca5db1fE7377",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "USDT_CONTRACT": {
            "abi": "./contracts/StixexUSDT.json",
            "address": "0xAB82007271685cc960a4Cc4417d716205C1779CE",#new"0xab82007271685cc960a4cc4417d716205c1779ce",#old"0x9401A439dBB12d0098eb765314E6D1A058BF2C43",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "ERC20_CONTRACT": {
            "abi": "./contracts/ERC20.json",
            "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "tracked_event_names": []
        },
        'ADMIN': '0x407B2364b5E727556C8c564F31686caDA0F9192b'
    },
    3: {
        "NODE_URL": "wss://ropsten.infura.io/ws/v3/5989bfec84544b4ba8ccca58cf9e9395",
        "ETH_CONTRACT": {
            "abi": "./contracts/StixexETH.json",
            "address": "0x053d1729b7Ed08Dd1394ffF1BC69a3E6afB1D7Ba",#"0xa6b4df8Da240f1F49d53840B6f7164125AFFe005", #"0x75D0BF66248626294d3De82F60673b695BbBB7eA",#"0x6263132F0b3d4c4dd26C67371286ef16BcCD801D",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "USDT_CONTRACT": {
            "abi": "./contracts/StixexUSDT.json",
            "address": "0xA69610Baf5bF3F9411d2fe79aFEe6daC0C4848C9", #"0xE646F7feB05D1C28bf79f26e15E491F3dcA01577",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "ERC20_CONTRACT": {
            "abi": "./contracts/ERC20.json",
            "address": "0x516de3a7a567d81737e3a46ec4ff9cfd1fcb0136", #"0x44eaFc17bfC14895d514Ad8b5D6a198B425cE34a",
            "tracked_event_names": []
        },
        'ADMIN': '0x407B2364b5E727556C8c564F31686caDA0F9192b'
    },
    4: {
        "NODE_URL": "wss://rinkeby.infura.io/ws/v3/de23f5f72bec4bf58268fccae1fd5a1d",
        "ETH_CONTRACT": {
            "abi": "./contracts/StixexETH.json",
            "address": "0x10b4Fa9845B302d6E8de08fC075616ccEf2FB424",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "USDT_CONTRACT": {
            "abi": "./contracts/StixexUSDT.json",
            "address": "0xfe07181a45CFf885AD4C3251FB07827AA1352222",
            "tracked_event_names": ['Deposited', 'Withdraw']
        },
        "ERC20_CONTRACT": {
            "abi": "./contracts/ERC20.json",
            "address": "0xb42c4a426106dd278da19aecd1faffbbdc0b69d8",
            "tracked_event_names": []
        },
        'ADMIN': '0x407B2364b5E727556C8c564F31686caDA0F9192b'
    }
}
