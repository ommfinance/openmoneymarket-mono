from .steps import Steps
import os
from dotenv import dotenv_values
ROOT = os.path.abspath(os.curdir)
ENV_PATH = os.path.abspath(os.path.join(ROOT, ".env.test"))
settings = dotenv_values(ENV_PATH)
EXA = 10 ** 18
NETWORK = settings["NETWORK"]
if NETWORK == "sejong":
    DELEGATION = [
            {
                '_address': 'hxfb687d33ab37768678d59ff47710f35348a1a4ec',
                '_votes_in_per': f'{20 * EXA // 100}'
            },
            {
                '_address': 'hxf539cd3511254468c8944313ac6a74859e6c2bf1',
                '_votes_in_per': f'{25 * EXA // 100}'
            },
            {
                '_address': 'hxe14cd6170fbf093acad0771e6d20676e9f85bd95',
                '_votes_in_per': f'{30 * EXA // 100}'
            },
            {
                '_address': 'hxd317634efef2c9a08638ce1702335020af82619a',
                '_votes_in_per': f'{25 * EXA // 100}'
            }
    ]
elif NETWORK == "goloop":
    DELEGATION = [
            {
                '_address': 'hxfa924ea2fd5ca2dcd58a61891797c18d8baa6913',
                '_votes_in_per': f'{20 * EXA // 100}'
            },
            {
                '_address': 'hxfa71d26259e11ff6b76c0550f6b92e9cc08621fd',
                '_votes_in_per': f'{25 * EXA // 100}'
            },
            {
                '_address': 'hxfa4207a8fb109f2e9f1ac91099edb3c2931ea612',
                '_votes_in_per': f'{30 * EXA // 100}'
            },
            {
                '_address': 'hxfe98328ee9f2535d086487026a48122b308612b5',
                '_votes_in_per': f'{25 * EXA // 100}'
            }
    ]

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
            "_delegations": DELEGATION,
            "expectedResult": 1
        },
        {
            "_step": Steps.CLEAR_DELEGATIONS,
            "user": "user1",
            "expectedResult": 1,
        },
    ]
}
