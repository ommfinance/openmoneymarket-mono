from .steps import Steps

EXA = 10 ** 18

ACTIONS = {
    "description": "Deposit 1000 ICX, Borrow 500 USDs, ICX price drops to $0.7, liquidation fail because of low balance of liquidator",
    "user":"new",
    "transaction": [
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "admin",  # user deployer can change the price oracle value
            "rate": 10 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "action": "deposit",
            "reserve": "sicx",
            "user": "borrower",
            "amount": 1000 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "action": "deposit",
            "reserve": "usds",
            "user": "liquidator",
            "amount": 5000 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "reserve": "usds",
            "user": "borrower",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "admin",
            "rate": 7 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
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
