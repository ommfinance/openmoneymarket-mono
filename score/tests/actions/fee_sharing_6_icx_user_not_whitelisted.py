from .steps import Steps
EXA = 10 ** 15

ACTIONS = {
    "description": "6. User1 has not deposited bridge dollars, so shouldn't get fee sharing.",
    "enableShare": 0, # whitelisted by bridge
    "transaction": [
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "user1",
            "amount": 500 * EXA // 1000,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "user1",
            "amount": 200 * EXA // 1000,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.REPAY_ICX,
            "user": "user1",
            "amount": 100 * EXA // 1000,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.REDEEM_ICX,
            "user": "user1",
            "amount": 100 * EXA // 1000,
            "expectedResult": 1,
            "feeShared": 0
        }        
    ]
}