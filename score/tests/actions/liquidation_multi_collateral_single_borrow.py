from .steps import Steps

EXA = 10 ** 18

ACTIONS = {
    "description": "2. Deposit 500 ICX, 500 USDb, Borrow 500 USDb, ICX price drops to $0.4, liquidation happens",
    "user": "new",
    "transaction": [
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "admin",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "borrower",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDB,
            "user": "borrower",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "liquidator",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDB,
            "user": "liquidator",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "liquidator",
            "amount": 300 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USBD,
            "user": "borrower",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "admin",
            "rate": 4 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.4 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "usdb",
            "expectedResult": 1
        }
    ]
}
