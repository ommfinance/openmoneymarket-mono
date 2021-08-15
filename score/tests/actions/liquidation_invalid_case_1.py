from .steps import Steps

EXA = 10 ** 18

ACTIONS = {
    "description": "Deposit 500 USDs, Borrow 250 USDs, Should not be liquidate",
    "user": "new",
    "transaction": [
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "borrower",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "liquidator",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "borrower",
            "amount": 250 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "usds",
            "expectedResult": 0,
            "errorCode": 32
        }
    ]
}
