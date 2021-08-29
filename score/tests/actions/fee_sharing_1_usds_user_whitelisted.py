from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "1. User1 has deposited some bridge in OMM\n    User1 is whitelisted in bridge.",
    "enableShare": 1, # whitelisted by bridge
    "transaction": [
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "user1",
            "amount": 500 * EXA,
            "expectedResult": 1,
            "remarks":"This transaction is is initiated by bridge token transfer, not on OMM lending pool. But since the user is whitelisted, they do not need to pay transaction fee.",
            "feeShared": 1
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
            "amount": 100 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REPAY_USDS,
            "user": "user1",
            "amount": 100 * EXA,
            "expectedResult": 1,
            "remarks":"This transaction is is initiated by bridge token transfer, not on OMM lending pool. But since the user is whitelisted, they do not need to pay transaction fee.",
            "feeShared": 1
        },
    ]
}