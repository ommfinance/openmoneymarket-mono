from .steps import Steps

EXA = 10 ** 18

ACTIONS = {
    "description": "",
    "transaction": [
        {
            "_step": Steps.STAKE_LP,
            "user": "user1",
            "amount": 100 * EXA // 100,
            "expectedResult": 1,
        },
        {
            "_step": Steps.UNSTAKE_LP,
            "user": "user1",
            "amount": 110 * EXA // 100,
            "expectedResult": 0
        },
        {
            "_step": Steps.UNSTAKE_LP,
            "user": "user1",
            "amount": 100 * EXA // 100,
            "expectedResult": 1,
        }, {
            "_step": Steps.STAKE_LP,
            "user": "user1",
            "amount": 500 * EXA // 100,
            "expectedResult": 1,
        },
        {
            "_step": Steps.UNSTAKE_LP,
            "user": "user1",
            "amount": 300 * EXA // 100,
            "expectedResult": 1,
        }
    ]
}
