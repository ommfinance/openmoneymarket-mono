# action = ["deposit","borrow","redeem","repay"]
# reserve = ["icx","usdb"]
# amount is in loop value

EXA = 10 ** 18

ACTIONS = {
    "description": "User deposits usdb and borrows usdb,tries different redeem and repay scenarios on the reserve,usdb price is 1$",
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
            "reserve": "usdb",
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
            "action": "redeem",
            "reserve": "usdb",
            "user": "new",
            "amount": 250 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which will drop health factor of user below 1",
            "revertMessage": "Redeem error:Transfer cannot be allowed"
        },
        {
            "action": "redeem",
            "reserve": "usdb",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "repay",
            "reserve": "usdb",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "repay",
            "reserve": "usdb",
            "user": "new",
            "amount": 500 * EXA,
            "expectedResult": 1,
            "remarks": "User tries to pay more than his loan,user should get the extra amount back to his wallet"
        }
    ]
}
