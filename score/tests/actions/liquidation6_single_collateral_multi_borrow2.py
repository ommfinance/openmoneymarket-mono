from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "6. Deposit 1000 USDs, Borrow 300 USDs, 200 ICX, ICX price increase to $2, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "borrower",
            "amount": 1 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "borrower",
            "amount": 3 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "borrower",
            "amount": 19 * EXA//100,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "liquidator",
            "amount": 1 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "liquidator",
            "amount": 5 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 2 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "icx",
            "expectedResult":1
        }
    ]}