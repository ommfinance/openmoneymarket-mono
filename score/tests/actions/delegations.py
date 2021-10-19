from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "Test for delegations",
    "transaction": [
        {
            "_step": Steps.STAKE_OMM,
            "user": "user1",
            "amount": 100 * EXA // 100,
            "expectedResult": 1,
        },
        {
            "_step": Steps.UPDATE_DELEGATIONS,
            "user": "user1",
            "_delegations": [
                {
                    '_address': 'hx00895a2f0947def33c944a6ff87684eb2e84c817',
                    '_votes_in_per': f'{20 * EXA // 100}'
                },
                {
                    '_address': 'hx02819422b1d5f92f79b49eb61dd8550d6207b9cb',
                    '_votes_in_per': f'{25 * EXA // 100}'
                },
                {
                    '_address': 'hx086fb1322da5c71422385b3a95da07f36ddaba0b',
                    '_votes_in_per': f'{30 * EXA // 100}'
                },
                {
                    '_address': 'hx0d3309744ad37bb040228981244e56d99eaf0d7a',
                    '_votes_in_per': f'{25 * EXA // 100}'
                }
            ],
            "expectedResult": 1
        },
        {
            "_step": Steps.CLEAR_DELEGATIONS,
            "user": "user1",
            "expectedResult": 1,
        },
    ]
}
