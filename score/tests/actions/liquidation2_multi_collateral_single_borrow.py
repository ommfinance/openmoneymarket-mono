from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "2. Deposit 500 ICX, 500 USDs, Borrow 500 USDs, ICX price drops to $0.4, liquidation happens",
    "transaction": [
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "borrower",
            "amount": 5 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "borrower",
            "amount": 5 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "liquidator",
            "amount": 5 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "liquidator",
            "amount": 5 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "liquidator",
            "amount": 3 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "borrower",
            "amount": 5 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",
            "rate": 4 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.4 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "usds",
            "expectedResult": 1
        }
    ]
}
