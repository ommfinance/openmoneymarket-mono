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
                    '_address': 'hx6347279a7f0356a058aa27343ee3fa471b1c042d' ,
                    '_votes_in_per': f'{20 * EXA // 100}'
                },
                {
                    '_address': 'hx60d55951dd8b6f4577a3fd17ba4040723e5e33c8' ,
                    '_votes_in_per': f'{25 * EXA // 100}'
                },
                {
                    '_address': 'hx4037b4d01c5bc40fdbb5217b8ef24fd35295aa37' ,
                    '_votes_in_per': f'{30 * EXA // 100}'
                },
                {
                    '_address': 'hx576bc82a94ed9e65828d6642fb3774536d81b348' ,
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