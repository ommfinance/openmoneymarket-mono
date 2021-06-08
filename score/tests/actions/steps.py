import enum


class Steps(enum.Enum):
    UPDATE_PRICE = 1
    DEPOSIT_USDB = 2
    DEPOSIT_ICX = 3
    BORROW_ICX = 4
    BORROW_USDB = 5
    LIQUIDATION = 6
