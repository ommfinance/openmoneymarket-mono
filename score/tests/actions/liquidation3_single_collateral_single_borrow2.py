from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "3. Deposit 1000 USDs, Borrow 500 ICX, ICX price increase to $1.4, liquidation happens",
    "transaction": [
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",  # user deployer can change the price oracle value
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "action": "deposit",
            "reserve": "usds",
            "user": "borrower",
            "amount": 1 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "reserve": "icx",
            "user": "liquidator",
            "amount": 31 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "reserve": "sicx",
            "user": "liquidator",
            "amount": 15 * EXA//10,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "action": "borrow",
            "reserve": "icx",
            "user": "borrower",
            "amount": 47 * EXA//100,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",  # user deployer can change the price oracle value
            "rate": 14 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1.4 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "call": "liquidation",
            "action": "transfer",
            "_collateral": "usds",
            "user": "liquidator",
            "_reserve": "icx",
            "expectedResult": 1
        }
    ]
}
