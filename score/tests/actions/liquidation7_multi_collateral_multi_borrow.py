from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "7. Deposit 800 USDs, 200 ICX, Borrow 100 USDs, 400 ICX, ICX price increase to $1.7, liquidation happens",
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
            "_step": Steps.DEPOSIT_USDS,
            "user": "borrower",
            "amount": 800 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "borrower",
            "amount": 200 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "borrower",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "borrower",
            "amount": 390 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "admin",
            "rate": 17 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        }, 
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "liquidator",
            "amount": 1000 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "liquidator",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "icx",
            "expectedResult":1
        }
    ]}