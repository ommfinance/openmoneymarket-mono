from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "OMM staking tests.",
    "transaction": [
        {   
            "_step": Steps.UPDATE_UNSTAKING_PERIOD,
            "user": "admin",
            "time": 0,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.ADD_TO_LOCKLIST,
            "user": "user1",
            "expectedResult": 1,
            "feeShared": 0
        },      
        {
            "_step": Steps.STAKE_OMM,
            "user": "user1",
            "amount": 120 * EXA,
            "expectedResult": 0,
            "feeShared": 0
        },
        {
            "_step": Steps.REMOVE_FROM_LOCKLIST,
            "user": "user1",
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.STAKE_OMM,
            "user": "user1",
            "amount": 100 * EXA, # 900 # 100
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.TRANSFER_OMM,
            "user": "user1",
            "amount": 990 * EXA, # 900 # 100
            "expectedResult": 0,
            "remarks": "User had 1000 OMM and staked 100. User should not be able to transfer 990 OMM tokens."
        },
        {   
            "_step": Steps.UNSTAKE_OMM,
            "user": "user1",
            "amount": 110 * EXA, # 900 # 100
            "expectedResult": 0,
            "feeShared": 0
        },
        {   
            "_step": Steps.UNSTAKE_OMM,
            "user": "user1",
            "amount": 10 * EXA, # 910 # 90 # 0
            "expectedResult": 1,
            "feeShared": 0
        },
        {   
            "_step": Steps.UPDATE_UNSTAKING_PERIOD,
            "user": "admin",
            "time": 100,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.UNSTAKE_OMM,
            "user": "user1",
            "amount": 10 * EXA, # 910 # 80 # 10
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.UNSTAKE_OMM,
            "user": "user1",
            "amount": 10 * EXA, # 910 # 80 # 10
            "expectedResult": 0,
            "feeShared": 0,
            "remarks": "Still in unstaking period, cannot stake before period has expired."
        },
        {
            "_step": Steps.SLEEP,
            "time": 100 # 920 # 80 # 0
        },
        {       
            "_step": Steps.DEPOSIT_USDS,
            "user": "user1",
            "amount": 10 * EXA, # 920 # 80 # 0
            "expectedResult": 1,
            "feeShared": 0
        },  
        {
            "_step": Steps.STAKE_OMM,
            "user": "user1",
            "amount": 120 * EXA, #880 # 120 # 0
            "expectedResult": 1,
            "feeShared": 1,
            "addedStake": 40 * EXA
        },
        {   
            "_step": Steps.UPDATE_UNSTAKING_PERIOD,
            "user": "admin",
            "time": 0,
            "expectedResult": 1,
            "feeShared": 0
        },
        {
            "_step": Steps.UNSTAKE_OMM,
            "user": "user1",
            "amount": 15 * EXA,
            "expectedResult": 1,
            "feeShared": 1
        }
    ]
}