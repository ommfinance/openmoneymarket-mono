from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "3. User1 has deposited some bridge in OMM\n    User1 is not whitelisted in bridge",
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
            "_step": Steps.BORROW_USDS,
            "user": "user1",
            "amount": 200 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REDEEM_USDS,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REDEEM_USDS,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REDEEM_USDS,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1,
            "remarks":"3 transactions is the limit set on install. User should pay fee for forth transaction.",
            "feeShared": 0
        },
        {
            "_step": Steps.REPAY_USDS,
            "user": "user1",
            "amount": 100 * EXA,
            "expectedResult": 1,
            "remarks":"This transaction is is initiated by bridge token transfer, not on OMM lending pool. So, user needs to pay fee. Also, free tx limit is over.",
            "feeShared": 0
        },
    ]
}