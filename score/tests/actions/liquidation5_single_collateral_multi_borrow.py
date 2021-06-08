from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "5. Deposit 1000 ICX, Borrow 300 USDb, 200 ICX, ICX price drops to $0.6, liquidation happens",
    "user":"new",
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
            "amount": 1000 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDB,
            "user": "borrower",
            "amount": 300 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "borrower",
            "amount": 190 * EXA, 
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "admin",
            "rate": 6 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.6 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "usdb",
            "expectedResult":1
        },
    ]}