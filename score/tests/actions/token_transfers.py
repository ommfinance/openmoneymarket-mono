from .steps import Steps

EXA = 10 ** 18

ACTIONS = {
    "description": "oToken and dToken transfer Operations",
    "transaction": [
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "user1",
            "amount": 500 * EXA // 100,
            "expectedResult": 1
        },
        {
            "_step": Steps.TRANSFER_OUSDS,
            "user": "user2",
            "to": "user1",
            "amount": 500 * EXA // 100,
            "expectedResult": 0,
            "revertMessage": "Insufficient Balance"
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "user2",
            "amount": 100 * EXA // 100,
            "expectedResult": 0,
            "revertMessage": "Borrow error:The user does not have any collateral"
        },
        {
            "_step": Steps.TRANSFER_OUSDS,
            "user": "user1",
            "to": "user2",
            "amount": 200 * EXA // 100,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "user2",
            "amount": 50 * EXA // 100,
            "expectedResult": 1,
        },
        {
            "_step": Steps.TRANSFER_DICX,
            "user": "user2",
            "to": "user1",
            "amount": 200 * EXA // 100,
            "expectedResult": 0,
            "revertMessage": "Debt Tokens are not transferable"            
        }
    ]
}
