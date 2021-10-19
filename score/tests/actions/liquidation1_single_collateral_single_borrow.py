from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "1. Deposit 1000 ICX, Borrow 500 USDs, ICX price drops to $0.7, liquidation happens (basic - most likely)",
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
            "_step": Steps.DEPOSIT_ICX,
            "user": "borrower",
            "amount": 1 * EXA,
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
            "rate": 7 * EXA // 10, 
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "usds",
            "expectedResult": 1 # now, liquidator has enough sicx to call liquidation 
        }, 
    ]}