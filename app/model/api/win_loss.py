from app.common.api_models import BaseApiModel


class WinLoss(BaseApiModel):
    eth_contract_balance: str = ""
    usdt_contract_balance: str = ""
    win_count: int = 0
    loss_count: int = 0
    draw_count: int = 0
    total_count: int = 0
    win_count_usdt: int = 0
    loss_count_usdt: int = 0
    draw_count_usdt: int = 0
    total_count_usdt: int = 0
    network_id: int = 0
    user_total_deposit_eth: str = ""
    user_total_deposit_usdt: str = ""
    user_total_withdraw_eth: str = ""
    user_total_withdraw_usdt: str = ""
    avg_eth: str = ""
    avg_usdt: str = ""
    win_eth: str = ""
    win_usdt: str = ""
    loss_eth: str = ""
    loss_usdt: str = ""
    avg_fee_eth: str = ""
    avg_fee_usdt: str = ""
    total_fee_eth: str = ""
    total_fee_usdt: str = ""
    total_eth_24: str = ""
    total_usdt_24: str = ""
    total_eth_week: str = ""
    total_usdt_week: str = ""
    total_eth_month: str = ""
    total_usdt_month: str = ""
    total_eth_3month: str = ""
    total_usdt_3month: str = ""
    total_eth_6month: str = ""
    total_usdt_6month: str = ""