from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "5. User1 has deposited some bridge in OMM",
    "enableShare": 1, # whitelisted by bridge
    "transaction": [
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "user1",
            "amount": 550 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "user1",
            "amount": 200 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REDEEM_ICX,
            "user": "user1",
            "amount": 100 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        },
        {
            "_step": Steps.REPAY_ICX,
            "user": "user1",
            "amount": 100 * EXA,
            "expectedResult": 1,
            "remarks":"3 free transaction limit exceeded. So user needs to pay.",
            "feeShared": 0
        },
    ]
}