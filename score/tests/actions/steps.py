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
    STAKE_LP = 11
    UNSTAKE_LP = 12
    STAKE_OMM = 13
    UNSTAKE_OMM = 14
    TRANSFER_OMM = 15