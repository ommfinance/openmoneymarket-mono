from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "Test for delegations",
    "transaction": [
        {
            "_step": Steps.STAKE_OMM,
            "user": "user1",
            "amount": 100 * EXA,
            "expectedResult": 1,
        },
        {
            "_step": Steps.UPDATE_DELEGATIONS,
            "user": "user1",
            "_delegations": [
                {
                    '_address': 'hxabcde924eba01ec91330e4e996cf7b8c658f4e4c' ,
                    '_votes_in_per': f'{20 * EXA // 100}'
                },
                {
                    '_address': 'hxbcdef924eba01ec91330e4e996cf7b8c658f4e4c' ,
                    '_votes_in_per': f'{25 * EXA // 100}'
                },
                {
                    '_address': 'hx12345924eba01ec91330e4e996cf7b8c658f4e4c' ,
                    '_votes_in_per': f'{30 * EXA // 100}'
                },
                {
                    '_address': 'hx23456924eba01ec91330e4e996cf7b8c658f4e4c' ,
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