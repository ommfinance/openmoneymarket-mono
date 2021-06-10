from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "1. User deposits icx and borrows icx,tries different redeem and repay scenarios on the reserve",
    "transactions": [
        {
            "_step": Steps.BORROW_ICX,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 0,
            "remarks": "User cannot borrow unless he has some deposit",
            "revertMessage": "Borrow error:The user does not have any collateral"
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "user1",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.REDEEM_ICX,
            "user": "user1",
            "amount": 25 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which will drop health factor of user below 1",
            "revertMessage": "Redeem error:Transfer cannot be allowed"
        },
        {
            "_step": Steps.REDEEM_ICX,
            "user": "user1",
            "amount": 10 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.REPAY_ICX,
            "user": "user1",
            "amount": 10 * EXA,
            "expectedResult": 1
        },
        {            
            "_step": Steps.REPAY_ICX,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1,
            "remarks": "User tries to pay more than his loan,user should get the extra amount back to his wallet"
        }
    ]
}
