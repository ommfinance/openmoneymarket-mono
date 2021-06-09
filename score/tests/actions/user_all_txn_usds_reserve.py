# action = ["deposit","borrow","redeem","repay"]
# reserve = ["icx","usds"]
# amount is in loop value

EXA = 10 ** 18

ACTIONS = {
    "description": "User deposits usds and borrows usds,tries different redeem and repay scenarios on the reserve,usds price is 1$",
    "user":"new",
    "transactions": [
        {
            "action": "borrow",
            "reserve": "usds",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 0,
            "remarks": "User cannot borrow unless he has some deposit",
            "revertMessage": "Borrow error:The user does not have any collateral"
        },
        {
            "action": "deposit",
            "reserve": "usds",
            "user": "new",
            "amount": 1000 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usds",
            "user": "new",
            "amount": 500 * EXA,
            "expectedResult": 1
        },
        {
            "action": "redeem",
            "reserve": "usds",
            "user": "new",
            "amount": 250 * EXA,
            "expectedResult": 0,
            "remarks": "Trying to redeem the asset which will drop health factor of user below 1",
            "revertMessage": "Redeem error:Transfer cannot be allowed"
        },
        {
            "action": "redeem",
            "reserve": "usds",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "repay",
            "reserve": "usds",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "repay",
            "reserve": "usds",
            "user": "new",
            "amount": 500 * EXA,
            "expectedResult": 1,
            "remarks": "User tries to pay more than his loan,user should get the extra amount back to his wallet"
        }
    ]
}
