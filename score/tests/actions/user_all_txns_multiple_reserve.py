from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "3. User deposits icx and borrows usdb, tries different redeem and repay scenarios on the reserve",
    "transactions": [
        {
            "_step": Steps.BORROW_USDS,
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
            "_step": Steps.BORROW_USDS,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.REDEEM_USDS,
            "user": "user1",
            "amount": 20 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which is not deposited by user",
            "revertMessage": "Redeem error:User cannot redeem more than the available balance"
        },
        {
           "_step": Steps.REDEEM_ICX,
            "user": "user1",
            "amount": 50 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which will drop health factor of user below 1",
            "revertMessage": "Redeem error:Transfer cannot be allowed"
        },
        {
            "_step": Steps.REDEEM_ICX,
            "user": "user1",
            "amount": 15 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.REPAY_ICX,
            "user": "user1",
            "amount": 10 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to repay loan which is not taken by the user",
            "revertMessage": "The user does not have any borrow pending"
        },
        {
            "_step": Steps.REPAY_USDS,
            "user": "user1",
            "amount": 10 * EXA,
            "expectedResult": 1
        }
    ]
}
