import enum


class Steps(enum.Enum):
    UPDATE_PRICE = 1
    DEPOSIT_USDS = 2
    DEPOSIT_ICX = 3
    BORROW_ICX = 4
    BORROW_USDS = 5
    LIQUIDATION = 6
    REDEEM_ICX = 7
    REPAY_ICX = 8
    REDEEM_USDS = 9
    REPAY_USDS = 10
    CLAIM_REWARDS = 11
    SLEEP = 12
