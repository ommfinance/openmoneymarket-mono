# action = ["deposit","borrow","redeem","repay"]
# reserve = ["icx","usdb"]
# amount is in loop value

EXA = 10 ** 18

ACTIONS = {
    "description": "User deposits icx and borrows usdb,tries different redeem and repay scenarios on the reserve",
    "user":"new",
    "transactions": [
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 0,
            "remarks": "User cannot borrow unless he has some deposit",
            "revertMessage": "Borrow error:The user does not have any collateral"
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
            "action": "redeem",
            "reserve": "usdb",
            "user": "new",
            "amount": 20 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which is not deposited by user",
            "revertMessage": "Redeem error:User cannot redeem more than the available balance"
        },
        {
            "action": "redeem",
            "reserve": "icx",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which will drop health factor of user below 1",
            "revertMessage": "Redeem error:Transfer cannot be allowed"
        },
        {
            "action": "redeem",
            "reserve": "icx",
            "user": "new",
            "amount": 15 * EXA,
            "expectedResult": 1
        },
        {
            "action": "repay",
            "reserve": "icx",
            "user": "new",
            "amount": 10 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to repay loan which is not taken by the user",
            "revertMessage": "The user does not have any borrow pending"
        },
        {
            "action": "repay",
            "reserve": "usdb",
            "user": "new",
            "amount": 10 * EXA,
            "expectedResult": 1
        }
    ]
}
