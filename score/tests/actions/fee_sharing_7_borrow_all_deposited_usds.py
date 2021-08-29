from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "7. User1 has deposits USDS and withdraws all.",
    "enableShare": 0, # not whitelisted by bridge
    "transaction": [
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "user1",
            "amount": 500 * EXA,
            "expectedResult": 1,
            "remarks":"This transaction is is initiated by bridge token transfer, not on OMM lending pool. So, user needs to pay fee.",
            "feeShared": 0
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "user1",
            "amount": 300 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REDEEM_USDS,
            "user": "user1",
            "amount": -1,
            "expectedResult": 1,
            "remarks":"User withdrew all USDS. Though 1 more free txn should remain after this txn, oUSDS balance is zero. So, no free txn remaining",
            "feeShared": 1
        },
        {
            "_step": Steps.BORROW_USDS,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1,
            "feeShared": 0,
            "remarks": "User has dUSDS but not oUSDS. So, fee not shared.",
        },
    ]
}