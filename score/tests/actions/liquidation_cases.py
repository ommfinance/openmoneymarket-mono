EXA = 10 ** 18

ACTIONS = {
    "description": "1. Deposit 1000 ICX, Borrow 500 USDb, ICX price drops to $0.7, liquidation happens (basic - most likely)",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": 1, # user 1 can change the price oracle value
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "icx",
            "user": "new",
            "amount": 1000 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": 1, # user 1 can change the price oracle value
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        }
    ]
}
