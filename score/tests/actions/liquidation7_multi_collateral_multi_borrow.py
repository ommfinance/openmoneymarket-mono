from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "7. Deposit 800 USDs, 200 ICX, Borrow 100 USDs, 400 ICX, ICX price increase to $1.7, liquidation happens",
    "user":"new",
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
            "_step": Steps.DEPOSIT_USDS,
            "user": "borrower",
            "amount": 8 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "borrower",
            "amount": 2* EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "borrower",
            "amount": 1 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "borrower",
            "amount": 39 * EXA//100,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",
            "rate": 17 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        }, 
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "liquidator",
            "amount": 1 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "liquidator",
            "amount": 47 * EXA//100,
            "expectedResult": 1
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "icx",
            "expectedResult":1
        }
    ]}