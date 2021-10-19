from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "5. Deposit 1000 ICX, Borrow 300 USDs, 200 ICX, ICX price drops to $0.6, liquidation happens",
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
            "amount": 10 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "borrower",
            "amount": 3 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "borrower",
            "amount": 19 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",
            "rate": 6 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.6 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "usds",
            "expectedResult":1
        },
    ]}