EXA = 10 ** 18

ACTIONS = {
    "description": "1. Deposit 1000 ICX, Borrow 500 USDb, ICX price drops to $0.7, liquidation happens (basic - most likely)",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", # user 1 can change the price oracle value
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "icx",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", # user 1 can change the price oracle value
            "rate": 7 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        },
        {
            "call":"liquidation",
            "action": "transfer",
            "_collateral": "icx",
            "reserve": "usdb",  # loan
            "borrower": "new", # borrower
            "liquidator": "deployer", # calls for liquidation
            "expectedResult": 1
        }
    ]
}
